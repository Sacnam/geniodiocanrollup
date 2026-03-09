"""
Text-to-Speech service with multiple providers for cost optimization.

This module implements a tiered TTS system:
1. Piper TTS (self-hosted) - Free tier, ~$0.01/1K chars
2. PlayHT Turbo - Mid tier, ~$0.03/1K chars
3. ElevenLabs - Premium tier, ~$0.10/1K chars

Cost Optimization Strategy:
- Free users: Piper TTS (self-hosted, practically free)
- Starter tier: PlayHT Turbo (good quality/price)
- Pro/Enterprise: ElevenLabs (best quality, custom voices)

Provider Comparison:
| Provider      | Cost/1M chars | Quality | Latency |
|---------------|---------------|---------|---------|
| Piper TTS     | ~$0.50        | ⭐⭐⭐   | 500ms   |
| PlayHT Turbo  | $1.50         | ⭐⭐⭐⭐ | 200ms   |
| ElevenLabs    | $11-20        | ⭐⭐⭐⭐⭐| 300ms   |
| Kokoro-82M    | ~$0.50        | ⭐⭐⭐⭐ | 400ms   |
"""
import hashlib
import io
import os
import tempfile
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import structlog

from app.core.config import settings
from app.core.redis import redis_client

logger = structlog.get_logger()


class TTSProvider(str, Enum):
    """Available TTS providers."""
    PIPER = "piper"           # Self-hosted, free
    KOKORO = "kokoro"         # Self-hosted, open source
    PLAYHT = "playht"         # Cloud, good quality/price
    ELEVENLABS = "elevenlabs" # Cloud, premium quality
    GOOGLE = "google"         # Google Cloud TTS
    AZURE = "azure"           # Azure Cognitive Services


class VoiceQuality(str, Enum):
    """Voice quality levels."""
    BASIC = "basic"           # Free tier
    STANDARD = "standard"     # Good quality
    PREMIUM = "premium"       # Best quality
    CUSTOM = "custom"         # Custom cloned voice


@dataclass
class TTSConfig:
    """Configuration for TTS synthesis."""
    provider: TTSProvider
    voice_id: str
    language: str
    speed: float = 1.0
    pitch: float = 1.0
    cost_per_1k_chars: float = 0.0
    max_chars_per_request: int = 5000
    supports_ssml: bool = False
    supports_streaming: bool = False


# Voice configurations
VOICE_CONFIGS = {
    # Piper voices (self-hosted, free)
    "piper_en_female": TTSConfig(
        provider=TTSProvider.PIPER,
        voice_id="en_US-lessac-medium",
        language="en-US",
        cost_per_1k_chars=0.001,  # Practically free
    ),
    "piper_en_male": TTSConfig(
        provider=TTSProvider.PIPER,
        voice_id="en_US-ryan-medium",
        language="en-US",
        cost_per_1k_chars=0.001,
    ),
    "piper_it_female": TTSConfig(
        provider=TTSProvider.PIPER,
        voice_id="it_IT-riccardo-x_low",  # Best Italian voice available
        language="it-IT",
        cost_per_1k_chars=0.001,
    ),
    
    # Kokoro voices (self-hosted, open source)
    "kokoro_en_female": TTSConfig(
        provider=TTSProvider.KOKORO,
        voice_id="af_bella",
        language="en-US",
        cost_per_1k_chars=0.002,
    ),
    "kokoro_en_male": TTSConfig(
        provider=TTSProvider.KOKORO,
        voice_id="am_adam",
        language="en-US",
        cost_per_1k_chars=0.002,
    ),
    
    # PlayHT voices (cloud, good quality)
    "playht_en_female": TTSConfig(
        provider=TTSProvider.PLAYHT,
        voice_id="jennifer",
        language="en-US",
        cost_per_1k_chars=0.003,  # $3/1M chars
        supports_streaming=True,
    ),
    "playht_en_male": TTSConfig(
        provider=TTSProvider.PLAYHT,
        voice_id="david",
        language="en-US",
        cost_per_1k_chars=0.003,
        supports_streaming=True,
    ),
    
    # ElevenLabs voices (cloud, premium)
    "elevenlabs_en_female": TTSConfig(
        provider=TTSProvider.ELEVENLABS,
        voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel
        language="en-US",
        cost_per_1k_chars=0.011,  # $11/1M chars
        supports_ssml=True,
        supports_streaming=True,
    ),
    "elevenlabs_en_male": TTSConfig(
        provider=TTSProvider.ELEVENLABS,
        voice_id="AZnzlk1XvdvUeBnXmlld",  # Domi
        language="en-US",
        cost_per_1k_chars=0.011,
        supports_ssml=True,
        supports_streaming=True,
    ),
    "elevenlabs_it_female": TTSConfig(
        provider=TTSProvider.ELEVENLABS,
        voice_id="IKne3meq5aSn9XLyUdCD",  # Charlie (multilingual)
        language="it-IT",
        cost_per_1k_chars=0.011,
        supports_ssml=True,
        supports_streaming=True,
    ),
}

# Default voice mapping by tier
DEFAULT_VOICES = {
    "free": "piper_en_female",
    "starter": "playht_en_female",
    "professional": "playht_en_female",
    "enterprise": "elevenlabs_en_female",
}


class TTSService:
    """
    Text-to-Speech service with intelligent provider selection.
    
    Features:
    - Automatic provider selection based on user tier
    - Caching to avoid regenerating same audio
    - Cost tracking per request
    - Fallback chain for reliability
    """
    
    def __init__(self):
        self._cache_prefix = "tts_cache:"
        self._cache_ttl = 86400 * 7  # 7 days
    
    def select_voice(
        self,
        user_tier: str,
        language: str = "en-US",
        preferred_voice: Optional[str] = None,
        user_credit_balance: int = 0,
    ) -> Tuple[TTSConfig, str]:
        """
        Select the optimal voice for a user.
        
        Args:
            user_tier: User subscription tier
            language: Target language
            preferred_voice: User's preferred voice
            user_credit_balance: Current credit balance
            
        Returns:
            Tuple of (TTSConfig, reason)
        """
        # If user has a preferred voice and it's available
        if preferred_voice and preferred_voice in VOICE_CONFIGS:
            config = VOICE_CONFIGS[preferred_voice]
            # Check if user can afford this voice
            if self._can_use_voice(config, user_tier, user_credit_balance):
                return config, "user_preference"
        
        # Select based on tier
        if user_tier == "enterprise":
            # Enterprise gets ElevenLabs
            voice_key = f"elevenlabs_{language.split('-')[0].lower()}_female"
            if voice_key not in VOICE_CONFIGS:
                voice_key = "elevenlabs_en_female"
            reason = "enterprise_tier"
        elif user_tier == "professional":
            # Pro gets PlayHT
            voice_key = f"playht_{language.split('-')[0].lower()}_female"
            if voice_key not in VOICE_CONFIGS:
                voice_key = "playht_en_female"
            reason = "professional_tier"
        elif user_tier == "starter":
            # Starter gets PlayHT basic
            voice_key = "playht_en_female"
            reason = "starter_tier"
        else:
            # Free tier gets Piper
            voice_key = f"piper_{language.split('-')[0].lower()}_female"
            if voice_key not in VOICE_CONFIGS:
                voice_key = "piper_en_female"
            reason = "free_tier"
        
        # Low balance override
        if user_credit_balance < 10 and user_tier in ["starter", "professional"]:
            voice_key = "piper_en_female"
            reason = "low_balance_optimization"
        
        return VOICE_CONFIGS[voice_key], reason
    
    def _can_use_voice(
        self,
        config: TTSConfig,
        user_tier: str,
        credit_balance: int,
    ) -> bool:
        """Check if user can use a specific voice."""
        # Enterprise can use any voice
        if user_tier == "enterprise":
            return True
        
        # Free tier can only use Piper/Kokoro
        if user_tier == "free":
            return config.provider in [TTSProvider.PIPER, TTSProvider.KOKORO]
        
        # Starter/Pro can use up to PlayHT
        if user_tier in ["starter", "professional"]:
            if config.provider == TTSProvider.ELEVENLABS:
                # Need sufficient credits for ElevenLabs
                return credit_balance >= 50
            return True
        
        return False
    
    def estimate_credits(self, text: str, config: TTSConfig) -> int:
        """
        Estimate credits needed for TTS synthesis.
        
        Args:
            text: Text to synthesize
            config: Voice configuration
            
        Returns:
            Estimated credits (1 credit = $0.01)
        """
        char_count = len(text)
        cost_usd = (char_count / 1000) * config.cost_per_1k_chars
        credits = max(1, int(cost_usd * 100))
        return credits
    
    def _get_cache_key(self, text: str, config: TTSConfig) -> str:
        """Generate cache key for text + voice combination."""
        text_hash = hashlib.sha256(f"{text}:{config.voice_id}".encode()).hexdigest()[:16]
        return f"{self._cache_prefix}{config.provider.value}:{text_hash}"
    
    async def synthesize(
        self,
        text: str,
        user_id: str,
        user_tier: str = "free",
        user_credit_balance: int = 0,
        language: str = "en-US",
        preferred_voice: Optional[str] = None,
        speed: float = 1.0,
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            user_id: User ID for tracking
            user_tier: User subscription tier
            user_credit_balance: Current credit balance
            language: Target language
            preferred_voice: User's preferred voice
            speed: Speech speed multiplier
            
        Returns:
            Tuple of (audio_bytes, metadata)
        """
        # Select voice
        config, selection_reason = self.select_voice(
            user_tier=user_tier,
            language=language,
            preferred_voice=preferred_voice,
            user_credit_balance=user_credit_balance,
        )
        
        # Estimate credits
        estimated_credits = self.estimate_credits(text, config)
        
        # Check balance
        if user_credit_balance < estimated_credits:
            raise InsufficientCreditsForTTS(
                f"Need {estimated_credits} credits for TTS, have {user_credit_balance}"
            )
        
        # Check cache
        cache_key = self._get_cache_key(text, config)
        cached_audio = await self._get_from_cache(cache_key)
        
        if cached_audio:
            metadata = {
                "provider": config.provider.value,
                "voice_id": config.voice_id,
                "selection_reason": selection_reason,
                "estimated_credits": 0,  # Cached = free
                "actual_credits": 0,
                "char_count": len(text),
                "from_cache": True,
            }
            return cached_audio, metadata
        
        # Synthesize based on provider
        start_time = time.time()
        
        try:
            if config.provider == TTSProvider.PIPER:
                audio_data, actual_cost = await self._synthesize_piper(text, config, speed)
            elif config.provider == TTSProvider.KOKORO:
                audio_data, actual_cost = await self._synthesize_kokoro(text, config, speed)
            elif config.provider == TTSProvider.PLAYHT:
                audio_data, actual_cost = await self._synthesize_playht(text, config, speed)
            elif config.provider == TTSProvider.ELEVENLABS:
                audio_data, actual_cost = await self._synthesize_elevenlabs(text, config, speed)
            else:
                raise ValueError(f"Unsupported TTS provider: {config.provider}")
            
            # Calculate actual credits
            actual_credits = max(1, int(actual_cost * 100))
            
            # Cache the result
            await self._save_to_cache(cache_key, audio_data)
            
            # Build metadata
            metadata = {
                "provider": config.provider.value,
                "voice_id": config.voice_id,
                "selection_reason": selection_reason,
                "estimated_credits": estimated_credits,
                "actual_credits": actual_credits,
                "actual_cost_usd": actual_cost,
                "char_count": len(text),
                "latency_ms": int((time.time() - start_time) * 1000),
                "from_cache": False,
            }
            
            logger.info(
                "tts_synthesis",
                user_id=user_id,
                **metadata
            )
            
            return audio_data, metadata
            
        except Exception as e:
            logger.error(
                "tts_synthesis_failed",
                user_id=user_id,
                provider=config.provider.value,
                error=str(e),
            )
            raise
    
    async def _synthesize_piper(
        self,
        text: str,
        config: TTSConfig,
        speed: float,
    ) -> Tuple[bytes, float]:
        """Synthesize using Piper TTS (self-hosted)."""
        try:
            import subprocess
            
            # Piper is a command-line tool
            # Install: pip install piper-tts
            voice_path = self._get_piper_voice_path(config.voice_id)
            
            # Create temp file for output
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                output_path = tmp.name
            
            try:
                # Run Piper
                cmd = [
                    "piper",
                    "--model", voice_path,
                    "--output_file", output_path,
                    "--noise_scale", str(0.667),
                    "--length_scale", str(1.0 / speed),  # Inverse for speed
                ]
                
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                
                stdout, stderr = process.communicate(input=text.encode('utf-8'))
                
                if process.returncode != 0:
                    raise RuntimeError(f"Piper failed: {stderr.decode()}")
                
                # Read output
                with open(output_path, 'rb') as f:
                    audio_data = f.read()
                
                # Estimate cost (practically free, just compute)
                cost = (len(text) / 1000) * 0.001  # ~$0.001/1K chars
                
                return audio_data, cost
                
            finally:
                # Cleanup
                if os.path.exists(output_path):
                    os.unlink(output_path)
                    
        except ImportError:
            # Piper not installed, use fallback
            logger.warning("piper_not_installed", message="Piper TTS not available, using fallback")
            return await self._synthesize_fallback(text, config, speed)
    
    def _get_piper_voice_path(self, voice_id: str) -> str:
        """Get path to Piper voice model."""
        # Check common locations
        piper_voices_dir = os.environ.get(
            'PIPER_VOICES_DIR',
            os.path.expanduser('~/.local/share/piper')
        )
        
        voice_path = os.path.join(piper_voices_dir, f"{voice_id}.onnx")
        
        if not os.path.exists(voice_path):
            # Download voice if not present
            logger.info("downloading_piper_voice", voice_id=voice_id)
            # In production, implement voice download logic
        
        return voice_path
    
    async def _synthesize_kokoro(
        self,
        text: str,
        config: TTSConfig,
        speed: float,
    ) -> Tuple[bytes, float]:
        """Synthesize using Kokoro TTS (self-hosted)."""
        # Kokoro-82M is a high-quality open-source TTS
        # Implementation would use the model directly
        try:
            # Placeholder for Kokoro implementation
            # In production, load model and generate
            raise NotImplementedError("Kokoro TTS not yet implemented")
        except Exception:
            return await self._synthesize_fallback(text, config, speed)
    
    async def _synthesize_playht(
        self,
        text: str,
        config: TTSConfig,
        speed: float,
    ) -> Tuple[bytes, float]:
        """Synthesize using PlayHT API."""
        import httpx
        
        api_key = getattr(settings, 'PLAYHT_API_KEY', None)
        if not api_key:
            return await self._synthesize_fallback(text, config, speed)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.play.ht/api/v2/tts",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "X-User-ID": getattr(settings, 'PLAYHT_USER_ID', ''),
                    "Content-Type": "application/json",
                },
                json={
                    "text": text,
                    "voice": config.voice_id,
                    "quality": "medium",
                    "output_format": "mp3",
                    "speed": speed,
                },
                timeout=30.0,
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"PlayHT API error: {response.text}")
            
            # Get audio URL from response
            result = response.json()
            audio_url = result.get("output", {}).get("url")
            
            if audio_url:
                # Download audio
                audio_response = await client.get(audio_url)
                audio_data = audio_response.content
            else:
                # Audio might be in response directly
                audio_data = response.content
            
            cost = (len(text) / 1000) * 0.003  # $3/1M chars
            
            return audio_data, cost
    
    async def _synthesize_elevenlabs(
        self,
        text: str,
        config: TTSConfig,
        speed: float,
    ) -> Tuple[bytes, float]:
        """Synthesize using ElevenLabs API."""
        import httpx
        
        api_key = getattr(settings, 'ELEVENLABS_API_KEY', None)
        if not api_key:
            return await self._synthesize_fallback(text, config, speed)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{config.voice_id}",
                headers={
                    "xi-api-key": api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75,
                        "style": 0.0,
                        "use_speaker_boost": True,
                    },
                },
                timeout=60.0,
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"ElevenLabs API error: {response.text}")
            
            audio_data = response.content
            cost = (len(text) / 1000) * 0.011  # $11/1M chars
            
            return audio_data, cost
    
    async def _synthesize_fallback(
        self,
        text: str,
        config: TTSConfig,
        speed: float,
    ) -> Tuple[bytes, float]:
        """Fallback synthesis using edge-tts (free)."""
        try:
            import edge_tts
            
            # Map to Edge TTS voices
            edge_voices = {
                "en-US": "en-US-AriaNeural",
                "en-GB": "en-GB-SoniaNeural",
                "it-IT": "it-IT-ElsaNeural",
                "de-DE": "de-DE-KatjaNeural",
                "fr-FR": "fr-FR-DeniseNeural",
                "es-ES": "es-ES-ElviraNeural",
            }
            
            voice = edge_voices.get(config.language, "en-US-AriaNeural")
            
            communicate = edge_tts.Communicate(text, voice)
            
            audio_chunks = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_chunks.append(chunk["data"])
            
            audio_data = b"".join(audio_chunks)
            cost = 0.0  # Edge TTS is free
            
            return audio_data, cost
            
        except ImportError:
            logger.error("edge_tts_not_available")
            raise RuntimeError("No TTS provider available")
    
    async def _get_from_cache(self, cache_key: str) -> Optional[bytes]:
        """Get audio from Redis cache."""
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                return cached
        except Exception as e:
            logger.warning("tts_cache_read_error", error=str(e))
        return None
    
    async def _save_to_cache(self, cache_key: str, audio_data: bytes) -> None:
        """Save audio to Redis cache."""
        try:
            await redis_client.setex(cache_key, self._cache_ttl, audio_data)
        except Exception as e:
            logger.warning("tts_cache_write_error", error=str(e))
    
    def get_available_voices(self, user_tier: str = "free") -> List[Dict[str, Any]]:
        """Get list of voices available for a user tier."""
        voices = []
        
        for name, config in VOICE_CONFIGS.items():
            # Check if voice is available for tier
            if user_tier == "free" and config.provider not in [TTSProvider.PIPER, TTSProvider.KOKORO]:
                continue
            
            voices.append({
                "id": name,
                "provider": config.provider.value,
                "language": config.language,
                "cost_per_1k_chars": config.cost_per_1k_chars,
                "supports_ssml": config.supports_ssml,
                "supports_streaming": config.supports_streaming,
            })
        
        return voices


class InsufficientCreditsForTTS(Exception):
    """Raised when user doesn't have enough credits for TTS."""
    pass


# Singleton instance
tts_service = TTSService()
