from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    BOT_TOKEN: SecretStr
    
    GOOGLE_API_KEY: SecretStr
    
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
        )

settings = Settings()