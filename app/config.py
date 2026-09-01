from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # required: no baked-in default, tool secret must come from the environment
    tool_secret: str
    # Optional, short-lived fallback for OloVoice saved tools created in the
    # dashboard, whose current editor does not expose custom HTTP headers.
    # Prefer X-Tool-Secret whenever the caller can set headers.
    olovoice_tool_token: str | None = None
    database_url: str = "sqlite:///./lale_bistro.db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
