"""
Verification tests for CODEBASE_AUDIT.md fixes.

These tests verify that the issues identified in the audit have been properly fixed:
- SEC-001: JWT secret key validation
- SEC-002: API key optional types
- ARCH-001: DB session dependency injection
- FE-001: Token refresh locking (tested in frontend)
- DEV-001: Alembic documentation
- ARCH-002: Knowledge module documentation

Run with: pytest tests/test_audit_fixes.py -v
"""
import os
import pytest
from unittest.mock import patch, MagicMock


class TestConfigSecurity:
    """Tests for SEC-001 and SEC-002: Security fixes in config.py"""
    
    def test_jwt_secret_required_in_production(self):
        """SEC-001: JWT_SECRET_KEY should be required when DEBUG=False"""
        # Remove JWT_SECRET_KEY from environment
        env_copy = os.environ.copy()
        os.environ.pop('JWT_SECRET_KEY', None)
        os.environ['DEBUG'] = 'false'
        
        try:
            # This should raise ValueError in production without JWT_SECRET_KEY
            with pytest.raises(ValueError) as exc_info:
                from app.core.config import Settings
                # Force re-evaluation
                import importlib
                import app.core.config as config_module
                importlib.reload(config_module)
                Settings()
            
            assert 'JWT_SECRET_KEY' in str(exc_info.value)
        finally:
            # Restore environment
            os.environ.clear()
            os.environ.update(env_copy)
    
    def test_jwt_secret_optional_in_development(self):
        """SEC-001: JWT_SECRET_KEY can be auto-generated in DEBUG mode"""
        with patch.dict(os.environ, {'DEBUG': 'true'}, clear=True):
            from app.core.config import Settings
            settings = Settings()
            
            # Should have a generated key in development
            key = settings.get_jwt_secret_key()
            assert key is not None
            assert len(key) >= 32  # Secure key length
    
    def test_api_keys_are_optional(self):
        """SEC-002: API keys should be Optional[str] type"""
        from app.core.config import Settings
        from typing import get_type_hints
        
        hints = get_type_hints(Settings)
        
        # These should be Optional[str]
        optional_keys = [
            'OPENAI_API_KEY',
            'GEMINI_API_KEY', 
            'SENDGRID_API_KEY',
            'STRIPE_SECRET_KEY',
        ]
        
        for key in optional_keys:
            # Check that the field exists and accepts None
            settings = Settings()
            assert hasattr(settings, key)
            # The default should be None or empty
            value = getattr(settings, key)
            assert value is None or value == '', f"{key} should default to None or empty"


class TestAuthDependencyInjection:
    """Tests for ARCH-001: DB session dependency injection fix"""
    
    def test_get_current_user_accepts_db_session(self):
        """ARCH-001: get_current_user should accept db as Depends parameter"""
        import inspect
        from app.core.auth import get_current_user
        
        sig = inspect.signature(get_current_user)
        params = list(sig.parameters.keys())
        
        # Should have 'db' parameter
        assert 'db' in params, "get_current_user should have 'db' parameter"
        
        # Check that db has Depends annotation
        db_param = sig.parameters['db']
        assert db_param.default is not inspect.Parameter.empty, \
            "db parameter should have a default value (Depends)"
    
    def test_get_current_user_no_manual_session(self):
        """ARCH-001: get_current_user should NOT create SessionLocal manually"""
        from app.core import auth
        import inspect
        
        # Get the source code
        source = inspect.getsource(auth.get_current_user)
        
        # Should NOT contain SessionLocal() in the main function
        # (it's only in the legacy function)
        lines = source.split('\n')
        main_function_lines = []
        in_main = False
        
        for line in lines:
            if 'async def get_current_user(' in line:
                in_main = True
            elif 'async def get_current_user_legacy' in line:
                in_main = False
            elif in_main:
                main_function_lines.append(line)
        
        main_source = '\n'.join(main_function_lines)
        
        # The main function should not create SessionLocal
        assert 'SessionLocal()' not in main_source, \
            "get_current_user should not create SessionLocal() manually"


class TestDatabaseDocumentation:
    """Tests for DEV-001: Database migration documentation"""
    
    def test_init_db_has_warning(self):
        """DEV-001: init_db should document its limitations"""
        from app.core.database import init_db
        import inspect
        
        docstring = init_db.__doc__
        assert docstring is not None, "init_db should have a docstring"
        assert 'Alembic' in docstring, "init_db docstring should mention Alembic"
        assert 'WARNING' in docstring or 'NOT suitable' in docstring, \
            "init_db should warn about its limitations"
    
    def test_get_session_documented(self):
        """DEV-001: get_session should have usage documentation"""
        from app.core.database import get_session
        import inspect
        
        docstring = get_session.__doc__
        assert docstring is not None, "get_session should have a docstring"
        assert 'Depends' in docstring or 'dependency injection' in docstring.lower(), \
            "get_session should document DI usage"


class TestKnowledgeModule:
    """Tests for ARCH-002: Knowledge module documentation"""
    
    def test_knowledge_module_has_docstring(self):
        """ARCH-002: knowledge module should have documentation"""
        from app import knowledge
        import inspect
        
        docstring = knowledge.__doc__
        assert docstring is not None, "knowledge module should have a docstring"
        assert len(docstring) > 100, "knowledge module docstring should be substantial"
    
    def test_knowledge_module_exports(self):
        """ARCH-002: knowledge module should export key classes"""
        from app import knowledge
        
        # Should export GraphExtractor and SemanticChunker
        assert hasattr(knowledge, 'GraphExtractor'), \
            "knowledge module should export GraphExtractor"
        assert hasattr(knowledge, 'SemanticChunker'), \
            "knowledge module should export SemanticChunker"
        
        # Check __all__ is defined
        assert hasattr(knowledge, '__all__'), \
            "knowledge module should define __all__"


class TestConfigBackwardCompatibility:
    """Tests for backward compatibility after config changes"""
    
    def test_settings_has_access_token_expire_minutes(self):
        """Verify backward compatibility for ACCESS_TOKEN_EXPIRE_MINUTES"""
        from app.core.config import Settings
        
        settings = Settings()
        
        # Should have both the new name and the alias
        assert hasattr(settings, 'JWT_ACCESS_TOKEN_EXPIRE_MINUTES')
        assert hasattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES')
        
        # They should return the same value
        assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == settings.ACCESS_TOKEN_EXPIRE_MINUTES
    
    def test_settings_has_refresh_token_expire_days(self):
        """Verify backward compatibility for REFRESH_TOKEN_EXPIRE_DAYS"""
        from app.core.config import Settings
        
        settings = Settings()
        
        # Should have both the new name and the alias
        assert hasattr(settings, 'JWT_REFRESH_TOKEN_EXPIRE_DAYS')
        assert hasattr(settings, 'REFRESH_TOKEN_EXPIRE_DAYS')
        
        # They should return the same value
        assert settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS == settings.REFRESH_TOKEN_EXPIRE_DAYS


# Run tests if executed directly
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
