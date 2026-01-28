"""
Configuration management for Ossi Voice AI.
Uses Claude (Anthropic) as the LLM provider.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Application Settings
    APP_NAME: str = "Ossi Voice AI"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = True
    
    # Claude (Anthropic) Configuration
    ANTHROPIC_API_KEY: str
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    CLAUDE_MAX_TOKENS: int = 4096
    
    # Twilio (Optional)
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://localhost:5432/ossi"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Safety & Performance
    CONFIDENCE_THRESHOLD: float = 0.7
    MAX_CONVERSATION_TURNS: int = 20
    SESSION_TIMEOUT_MINUTES: int = 30
    
    # Feature Flags
    ENABLE_RECORDING: bool = True
    ENABLE_TRIAGE: bool = True
    ENABLE_MULTILINGUAL: bool = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


if __name__ == "__main__":
    settings = get_settings()
    print("=" * 50)
    print("Ossi Voice AI - Configuration Test")
    print("=" * 50)
    print(f"App Name: {settings.APP_NAME}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Claude Model: {settings.CLAUDE_MODEL}")
    print(f"Claude API Key Set: {'Yes ✅' if settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY != 'your-claude-api-key-here' else 'No ❌'}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"Max Tokens: {settings.CLAUDE_MAX_TOKENS}")
    print("=" * 50)
    print("✅ Configuration loaded successfully!")
