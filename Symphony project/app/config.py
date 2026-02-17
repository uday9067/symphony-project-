import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # App settings
    app_name: str = "Project Symphony"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Free AI APIs
    google_api_key: Optional[str] = os.getenv("GOOGLE_API_KEY")
    huggingface_token: Optional[str] = os.getenv("HUGGINGFACE_TOKEN")
    
    # Model selection (use free models)
    default_model: str = "gemini-pro"  # Free from Google
    fallback_model: str = "huggingface"  # Free from Hugging Face
    
    # Project settings
    max_iterations: int = 3
    timeout_seconds: int = 300
    output_dir: str = "generated_projects"
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./project_symphony.db"
    
    class Config:
        env_file = ".env"

settings = Settings()

# Validate free API keys
if not settings.google_api_key and not settings.huggingface_token:
    print("⚠️  Warning: No free API keys found. Please get free keys from:")
    print("Google AI Studio: https://makersuite.google.com/app/apikey")
    print("Hugging Face: https://huggingface.co/settings/tokens")