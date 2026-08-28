from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Reservation, ReservationStatus, RestaurantTable
from app.timeutil import now_istanbul_naive

RESERVATION_MINUTES = 90
OPEN_HOUR = 12
LAST_START_HOUR, LAST_START_MINUTE = 21, 30
CLOSED_WEEKDAY = 0  # Monday


def validate_requested_time(local_time: datetime) -> tuple[bool, str | None]:
    if local_time < now_istanbul_naive():
        return False, "past_time"
    if local_time.weekday() == CLOSED_WEEKDAY:
        return False, "closed_monday"
    opening = local_time.replace(hour=OPEN_HOUR, minute=0, second=0, microsecond=0)
    last_start = local_time.replace(
        hour=LAST_START_HOUR, minute=LAST_START_MINUTE, second=0, microsecond=0
    )
    if local_time < opening or local_time > last_start:
        return False, "outside_opening_hours"
    return True, None


def find_available_table(
    db: Session, start: datetime, party_size: int
) -> RestaurantTable | None:
    end = start + timedelta(minutes=RESERVATION_MINUTES)
    tables = (
        db.execute(
            select(RestaurantTable)
            .where(RestaurantTable.capacity >= party_size)
            .order_by(RestaurantTable.capacity.asc(), RestaurantTable.id.asc())
        )
        .scalars()
        .all()
    )
    for table in tables:
        overlap = db.execute(
            select(Reservation.id).where(
                Reservation.table_id == table.id,
                Reservation.status == ReservationStatus.CONFIRMED,
                Reservation.start_time < end,
                Reservation.end_time > start,
            )
        ).first()
        if overlap is None:
            return table
    return None


def suggest_alternatives(
    db: Session, requested: datetime, party_size: int, limit: int = 3
) -> list[datetime]:
    # ponytail: same-day grid only, no cross-day search. Good enough for a
    # demo; extend to "next open day" if same-day options run out.
    day_start = requested.replace(hour=OPEN_HOUR, minute=0, second=0, microsecond=0)
    last_start = requested.replace(
        hour=LAST_START_HOUR, minute=LAST_START_MINUTE, second=0, microsecond=0
    )
    now = now_istanbul_naive()

    slots = []
    slot = day_start
    while slot <= last_start:
        if slot != requested and slot >= now:
            slots.append(slot)
        slot += timedelta(minutes=30)

    slots.sort(key=lambda s: abs((s - requested).total_seconds()))

    alternatives = []
    for candidate in slots:
        if find_available_table(db, candidate, party_size) is not None:
            alternatives.append(candidate)
        if len(alternatives) >= limit:
            break

    alternatives.sort()
    return alternatives
