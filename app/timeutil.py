from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Istanbul")


def now_istanbul() -> datetime:
    return datetime.now(TZ)


def now_istanbul_naive() -> datetime:
    return now_istanbul().replace(tzinfo=None)


def to_naive_istanbul(dt: datetime) -> datetime:
    """Interpret a naive datetime as already-Istanbul-local; convert aware ones."""
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(TZ).replace(tzinfo=None)


def to_aware_istanbul(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        return dt.astimezone(TZ)
    return dt.replace(tzinfo=TZ)
