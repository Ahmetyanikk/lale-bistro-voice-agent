from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # required: no baked-in default, tool secret must come from the environment
    tool_secret: str
    database_url: str = "sqlite:///./lale_bistro.db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
