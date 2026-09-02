import re
import secrets

# no O/0/I/1: avoids ambiguous characters when read aloud or typed back
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_confirmation_code() -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(4))


def normalize_confirmation_code(value: str) -> str:
    """Return the canonical four-character form used by the API.

    Voice transcription and LLM tool calls may insert spaces or punctuation
    while spelling the code. The old ``LBL-`` form remains accepted only for
    backwards compatibility with reservations created by earlier versions.
    """
    compact = re.sub(r"[^A-Z0-9]", "", value.upper())
    if compact.startswith("LBL"):
        compact = compact[3:]
    if len(compact) == 4:
        return compact
    return value.strip().upper()


def confirmation_code_lookup_values(value: str) -> tuple[str, ...]:
    """Return current and legacy database values for a supplied code."""
    code = normalize_confirmation_code(value)
    if re.fullmatch(r"[A-Z0-9]{4}", code):
        return code, f"LBL-{code}"
    return (code,)
