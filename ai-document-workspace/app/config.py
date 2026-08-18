from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    DATABASE_URL: str
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-3.5-flash"
    UPLOAD_FOLDER: str

    model_config = SettingsConfigDict(
        env_file=".env"
    )


settings = Settings()
