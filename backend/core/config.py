"""
Application configuration.
"""

import os
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from a .env file
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """
    Application settings, loaded from environment variables.
    """

    # Application Configuration
    app_name: str = "Mycel"
    app_env: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    # JWT Authentication Configuration
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # MongoDB Configuration
    mongodb_url: str = "mongodb://localhost:27017/office"
    mongodb_database: str = "office"

    # ArmorIQ / Security Configuration
    armoriq_api_key: str = ""
    security_provider_mode: str = "armoriq"  # 'armoriq' or 'mock'
    armoriq_timeout_ms: int = 5000

    # Gemini Configuration
    gemini_api_key: str = ""
    gemini_api_key_2: str = ""

    # Groq Configuration
    groq_api_key: str = ""
    groq_api_key_1: str = ""
    groq_api_key_2: str = ""

    # Team-level Groq API keys (comma-separated lists, e.g. "key1,key2")
    # If a team key is not set, falls back to the global groq_api_key_1/2
    groq_creative_keys: str = ""
    groq_engineering_keys: str = ""
    groq_operations_keys: str = ""
    groq_sales_keys: str = ""
    groq_hr_keys: str = ""
    groq_research_keys: str = ""
    groq_marketing_keys: str = ""
    # Groq Extreme Global Pool
    groq_extreme_pool: str = ""
    groq_max_concurrency: int = 3

    # Council Agent specific keys
    groq_api_key_helena: str = ""
    groq_api_key_vikram: str = ""
    groq_api_key_nisha: str = ""
    groq_api_key_omar: str = ""
    groq_api_key_sofia: str = ""
    
    # Intelligence Agent specific keys
    groq_api_key_mira: str = ""
    groq_api_key_ravi: str = ""
    groq_api_key_anika: str = ""
    groq_api_key_noor: str = ""

    # Network Agent specific keys
    groq_api_key_aanya: str = ""
    groq_api_key_dev: str = ""
    groq_api_key_kabir: str = ""
    groq_api_key_tara: str = ""

    # Real Estate Domain Demo
    re_voice_mode: str = "browser"              # "browser" | "voicelink" | "groq_whisper"
    re_demo_customer_id: str = "kaushal"
    re_collection_properties: str = "re_properties"
    re_collection_ingestion_jobs: str = "re_ingestion_jobs"
    re_max_search_results: int = 50
    re_legal_kb_version: int = 1
    re_max_upload_size_mb: int = 50

    # RabbitMQ Configuration
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    rabbitmq_vhost: str = "/"

    # Storage (Cloudinary)
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""

    # Redis (Optional cache)
    redis_url: str = ""

    # ComfyUI Image Generation
    comfyui_base_url: str = "http://127.0.0.1:8188"
    comfyui_api_key: Optional[str] = None
    comfyui_timeout_seconds: int = 180
    comfyui_max_retries: int = 2
    comfyui_default_width: int = 512
    comfyui_default_height: int = 512
    comfyui_default_steps: int = 25
    comfyui_live_test: bool = False

    # ComfyUI Video Generation (Wan 2.1 1.3B — ~8GB VRAM for 480P)
    comfyui_wan_model: str = "wan2.1-i2v-1.3B-480P.safetensors"
    comfyui_video_default_fps: int = 16
    comfyui_video_max_duration: int = 8   # seconds; hard cap for 8GB VRAM safety

    # Cloudflare Image Worker
    cloudflare_image_worker_url: str = "https://image-gen.kaushaljindal07.workers.dev/"
    cloudflare_image_worker_key: Optional[str] = None

    # External Tools APIs
    serper_api_key: str = ""
    firecrawl_api_key: str = ""
    openweathermap_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=env_path,
        env_file_encoding="utf-8",
        extra="ignore"
    )

# This single instance will be used across the application
# Pydantic will validate the types of the environment variables
settings = Settings()
