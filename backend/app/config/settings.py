import os

class Settings:
    # FastAPI配置
    API_PREFIX = "/api/v1/audio-editor"
    PROJECT_NAME = "sound-Edit"
    DEBUG = True

    # Celery配置
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

    # 音频处理相关
    AUDIO_OUTPUT_DIR = os.getenv("AUDIO_OUTPUT_DIR", "./outputs")
    FFmpeg_BIN = os.getenv("FFMPEG_BIN", "ffmpeg")
    
    # 数据库配置
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sound_edit.db")

settings = Settings()
