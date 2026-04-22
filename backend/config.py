from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    VLLM_BASE_URL: str = "http://localhost:11434/v1"
    VLLM_MODEL_NAME: str = "qwen"
    VLLM_API_KEY: str = "EMPTY"
    LLM_MAX_TOKENS: int = 8192
    MAX_UPLOAD_FILES: int = 20
    MAX_FILE_SIZE_MB: int = 10

    class Config:
        env_file = ".env"


settings = Settings()
