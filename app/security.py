import secrets

from fastapi import Header, HTTPException

from app.config import settings


def require_tool_secret(x_tool_secret: str | None = Header(default=None)) -> None:
    if not x_tool_secret or not secrets.compare_digest(x_tool_secret, settings.tool_secret):
        raise HTTPException(status_code=401, detail={"error": "invalid_tool_secret"})
