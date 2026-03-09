"""
Modular AI provider system for LLM and TTS.
Allows hot-swapping providers without code changes.
"""
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import aiohttp
import openai
from app.core.config import settings


class ProviderType(str, Enum):
    LLM = "llm"
    TTS = "tts"
    EMBEDDING = "embedding"


@dataclass
class ProviderConfig:
    """Configuration for an AI provider."""
    name: str
    provider_type: ProviderType
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    voice: Optional[str] = None  # For TTS
    extra_params: Dict[str, Any] = None
    priority: int = 1  # Lower = higher priority
    enabled: bool = True
    cost_per_1k_tokens: float = 0.0
    max_concurrent: int = 10


class BaseProvider(ABC):
    """Base class for all AI providers."""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text completion."""
        pass
    
    @abstractmethod
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream text generation."""
        pass


class OpenAIProvider(BaseProvider):
    """OpenAI GPT provider."""
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        client = openai.AsyncOpenAI(api_key=self.config.api_key)
        response = await client.chat.completions.create(
            model=self.config.model or "gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.choices[0].message.content
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        client = openai.AsyncOpenAI(api_key=self.config.api_key)
        stream = await client.chat.completions.create(
            model=self.config.model or "gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            **kwargs
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def generate_speech(self, text: str, **kwargs) -> bytes:
        """TTS via OpenAI."""
        client = openai.AsyncOpenAI(api_key=self.config.api_key)
        response = await client.audio.speech.create(
            model="tts-1",
            voice=self.config.voice or "alloy",
            input=text,
            **kwargs
        )
        return response.content


class AnthropicProvider(BaseProvider):
    """Anthropic Claude provider."""
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        headers = {
            "x-api-key": self.config.api_key,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        data = {
            "model": self.config.model or "claude-3-sonnet-20240229",
            "max_tokens": kwargs.get("max_tokens", 4096),
            "messages": [{"role": "user", "content": prompt}]
        }
        
        async with self.session.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data
        ) as response:
            result = await response.json()
            return result["content"][0]["text"]


class GeminiProvider(BaseProvider):
    """Google Gemini provider."""
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        import google.generativeai as genai
        genai.configure(api_key=self.config.api_key)
        model = genai.GenerativeModel(self.config.model or "gemini-pro")
        response = await model.generate_content_async(prompt)
        return response.text


class ElevenLabsTTSProvider(BaseProvider):
    """ElevenLabs premium TTS."""
    
    async def generate_speech(self, text: str, **kwargs) -> bytes:
        voice_id = self.config.voice or "21m00Tcm4TlvDq8ikWAM"  # Rachel
        
        async with self.session.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": self.config.api_key},
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": kwargs.get("stability", 0.5),
                    "similarity_boost": kwargs.get("similarity_boost", 0.75)
                }
            }
        ) as response:
            return await response.read()


class CoquiTTSProvider(BaseProvider):
    """Coqui TTS (Open Source, self-hosted option)."""
    
    async def generate_speech(self, text: str, **kwargs) -> bytes:
        """Call local Coqui TTS server."""
        async with self.session.post(
            f"{self.config.base_url}/api/tts",
            json={
                "text": text,
                "speaker_id": kwargs.get("speaker_id"),
                "language_id": kwargs.get("language_id", "en")
            }
        ) as response:
            return await response.read()


class LocalLLMProvider(BaseProvider):
    """Local LLM via Ollama or similar."""
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        async with self.session.post(
            f"{self.config.base_url}/api/generate",
            json={
                "model": self.config.model or "llama2",
                "prompt": prompt,
                "stream": False
            }
        ) as response:
            result = await response.json()
            return result["response"]
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        async with self.session.post(
            f"{self.config.base_url}/api/generate",
            json={
                "model": self.config.model or "llama2",
                "prompt": prompt,
                "stream": True
            }
        ) as response:
            async for line in response.content:
                if line:
                    import json
                    data = json.loads(line)
                    if "response" in data:
                        yield data["response"]


class AIProviderManager:
    """Manages multiple AI providers with failover and load balancing."""
    
    def __init__(self):
        self.providers: Dict[str, BaseProvider] = {}
        self.configs: Dict[str, ProviderConfig] = {}
        self._load_providers()
    
    def _load_providers(self):
        """Load provider configurations from environment/database."""
        # Default providers from settings
        providers = [
            # LLM Providers
            ProviderConfig(
                name="openai",
                provider_type=ProviderType.LLM,
                api_key=settings.OPENAI_API_KEY,
                model="gpt-4o",
                priority=1
            ),
            ProviderConfig(
                name="anthropic",
                provider_type=ProviderType.LLM,
                api_key=settings.ANTHROPIC_API_KEY,
                model="claude-3-sonnet-20240229",
                priority=2
            ),
            ProviderConfig(
                name="gemini",
                provider_type=ProviderType.LLM,
                api_key=settings.GEMINI_API_KEY,
                model="gemini-pro",
                priority=3
            ),
            # TTS Providers
            ProviderConfig(
                name="elevenlabs",
                provider_type=ProviderType.TTS,
                api_key=settings.ELEVENLABS_API_KEY,
                voice=settings.ELEVENLABS_VOICE_ID,
                priority=1
            ),
            ProviderConfig(
                name="openai_tts",
                provider_type=ProviderType.TTS,
                api_key=settings.OPENAI_API_KEY,
                voice="alloy",
                priority=2
            ),
            ProviderConfig(
                name="coqui",
                provider_type=ProviderType.TTS,
                base_url=settings.COQUI_TTS_URL,
                priority=3
            ),
        ]
        
        for config in providers:
            if config.api_key or config.base_url:
                self._register_provider(config)
    
    def _register_provider(self, config: ProviderConfig):
        """Register a provider instance."""
        self.configs[config.name] = config
        
        if config.provider_type == ProviderType.LLM:
            if "openai" in config.name:
                self.providers[config.name] = OpenAIProvider(config)
            elif "anthropic" in config.name:
                self.providers[config.name] = AnthropicProvider(config)
            elif "gemini" in config.name:
                self.providers[config.name] = GeminiProvider(config)
            elif "local" in config.name:
                self.providers[config.name] = LocalLLMProvider(config)
        
        elif config.provider_type == ProviderType.TTS:
            if "elevenlabs" in config.name:
                self.providers[config.name] = ElevenLabsTTSProvider(config)
            elif "openai" in config.name:
                self.providers[config.name] = OpenAIProvider(config)
            elif "coqui" in config.name:
                self.providers[config.name] = CoquiTTSProvider(config)
    
    async def generate_text(
        self,
        prompt: str,
        provider_type: ProviderType = ProviderType.LLM,
        preferred_provider: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text with automatic failover."""
        
        providers = [
            name for name, config in self.configs.items()
            if config.provider_type == provider_type and config.enabled
        ]
        
        if preferred_provider and preferred_provider in providers:
            providers.insert(0, preferred_provider)
        
        # Sort by priority
        providers.sort(key=lambda x: self.configs[x].priority)
        
        last_error = None
        for provider_name in providers:
            provider = self.providers.get(provider_name)
            if not provider:
                continue
            
            try:
                async with provider:
                    result = await provider.generate_text(prompt, **kwargs)
                    return {
                        "text": result,
                        "provider": provider_name,
                        "success": True
                    }
            except Exception as e:
                last_error = e
                continue
        
        return {
            "error": str(last_error),
            "success": False
        }
    
    async def generate_speech(
        self,
        text: str,
        preferred_provider: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate speech with failover."""
        
        result = await self.generate_text(
            text,
            provider_type=ProviderType.TTS,
            preferred_provider=preferred_provider,
            **kwargs
        )
        
        if result.get("success"):
            return {
                "audio": result["text"],  # Actually bytes for TTS
                "provider": result["provider"],
                "success": True
            }
        
        return result
    
    def get_available_providers(self, provider_type: ProviderType) -> List[str]:
        """Get list of available providers for a type."""
        return [
            name for name, config in self.configs.items()
            if config.provider_type == provider_type and config.enabled
        ]
    
    def update_provider_config(self, name: str, **kwargs):
        """Update provider configuration at runtime."""
        if name in self.configs:
            for key, value in kwargs.items():
                setattr(self.configs[name], key, value)


# Global instance
ai_manager = AIProviderManager()
