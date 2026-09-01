import secrets

from fastapi import Header, HTTPException, Query

from app.config import settings


def require_tool_secret(
    x_tool_secret: str | None = Header(default=None),
    tool_token: str | None = Query(default=None),
) -> None:
    """Authenticate tool calls by header, or by the dashboard-only fallback.

    The query token is deliberately optional and disabled unless
    OLOVOICE_TOOL_TOKEN is configured. It exists because OloVoice's saved-tool
    dashboard currently exposes a webhook URL but not custom request headers.
    """

    header_is_valid = bool(x_tool_secret) and secrets.compare_digest(
        x_tool_secret, settings.tool_secret
    )
    query_is_valid = (
        bool(settings.olovoice_tool_token)
        and bool(tool_token)
        and secrets.compare_digest(tool_token, settings.olovoice_tool_token)
    )
    if not (header_is_valid or query_is_valid):
        raise HTTPException(status_code=401, detail={"error": "invalid_tool_secret"})
