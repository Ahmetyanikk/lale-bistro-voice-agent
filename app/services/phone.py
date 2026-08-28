import re


def normalize_turkish_phone(raw: str) -> str:
    """Best-effort normalize to E.164. Handles common Turkish formats
    (0532..., +90532..., 90532..., 532...). Falls back to the original
    string, trimmed, when it can't confidently be normalized.
    """
    raw = raw.strip()
    digits = re.sub(r"\D", "", raw)

    if digits.startswith("90") and len(digits) == 12:
        digits = digits[2:]
    elif digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]

    if len(digits) == 10:
        return f"+90{digits}"
    if raw.startswith("+") and digits:
        return f"+{digits}"
    return raw
