from datetime import datetime, timedelta

from app.timeutil import TZ


def next_open_datetime(hour: int = 19, minute: int = 0, days_ahead: int = 1) -> datetime:
    dt = datetime.now(TZ).replace(hour=hour, minute=minute, second=0, microsecond=0)
    dt += timedelta(days=days_ahead)
    while dt.weekday() == 0:  # skip Monday
        dt += timedelta(days=1)
    return dt


def next_monday_datetime(hour: int = 19, minute: int = 0) -> datetime:
    dt = datetime.now(TZ).replace(hour=hour, minute=minute, second=0, microsecond=0)
    dt += timedelta(days=1)
    while dt.weekday() != 0:
        dt += timedelta(days=1)
    return dt
