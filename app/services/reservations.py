import threading
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Reservation, ReservationStatus
from app.services.availability import (
    RESERVATION_MINUTES,
    find_available_table,
    suggest_alternatives,
    validate_requested_time,
)
from app.services.codes import generate_confirmation_code
from app.services.phone import normalize_turkish_phone
from app.timeutil import to_naive_istanbul

# ponytail: process-wide lock serializes the check-then-create critical
# section. SQLite has no cheap row-range locking for overlap checks; this is
# correct for a single-process demo. Swap for `SELECT ... FOR UPDATE` on the
# table if this ever runs multi-process against Postgres.
_reservation_lock = threading.Lock()


def _unique_code(db: Session) -> str:
    for _ in range(20):
        code = generate_confirmation_code()
        exists = db.execute(
            select(Reservation.id).where(Reservation.confirmation_code == code)
        ).first()
        if not exists:
            return code
    raise RuntimeError("could not generate a unique confirmation code")


def _existing_to_result(existing: Reservation) -> dict:
    return {
        "status": "confirmed" if existing.status == ReservationStatus.CONFIRMED else "cancelled",
        "reason": None,
        "table": existing.table,
        "start": existing.start_time,
        "end": existing.end_time,
        "code": existing.confirmation_code,
        "alternatives": [],
    }


def check_availability(db: Session, party_size: int, requested_time: datetime) -> dict:
    local_time = to_naive_istanbul(requested_time)
    ok, reason = validate_requested_time(local_time)
    if not ok:
        return {"available": False, "table": None, "reason": reason, "alternatives": []}

    table = find_available_table(db, local_time, party_size)
    if table is not None:
        return {"available": True, "table": table, "reason": None, "alternatives": []}

    alternatives = suggest_alternatives(db, local_time, party_size)
    return {"available": False, "table": None, "reason": "no_availability", "alternatives": alternatives}


def create_reservation(
    db: Session,
    tool_call_id: str,
    customer_name: str,
    phone: str,
    party_size: int,
    requested_time: datetime,
) -> dict:
    existing = db.execute(
        select(Reservation).where(Reservation.tool_call_id == tool_call_id)
    ).scalar_one_or_none()
    if existing is not None:
        return _existing_to_result(existing)

    local_time = to_naive_istanbul(requested_time)
    ok, reason = validate_requested_time(local_time)
    if not ok:
        return {
            "status": "rejected", "reason": reason, "table": None,
            "start": None, "end": None, "code": None, "alternatives": [],
        }

    phone_norm = normalize_turkish_phone(phone)
    end_time = local_time + timedelta(minutes=RESERVATION_MINUTES)

    with _reservation_lock:
        table = find_available_table(db, local_time, party_size)
        if table is None:
            alternatives = suggest_alternatives(db, local_time, party_size)
            return {
                "status": "rejected", "reason": "no_availability", "table": None,
                "start": None, "end": None, "code": None, "alternatives": alternatives,
            }

        code = _unique_code(db)
        reservation = Reservation(
            tool_call_id=tool_call_id,
            confirmation_code=code,
            customer_name=customer_name,
            phone=phone_norm,
            party_size=party_size,
            table_id=table.id,
            start_time=local_time,
            end_time=end_time,
            status=ReservationStatus.CONFIRMED,
        )
        db.add(reservation)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            existing = db.execute(
                select(Reservation).where(Reservation.tool_call_id == tool_call_id)
            ).scalar_one_or_none()
            if existing is not None:
                return _existing_to_result(existing)
            raise
        db.refresh(reservation)

    return {
        "status": "confirmed", "reason": None, "table": table,
        "start": reservation.start_time, "end": reservation.end_time,
        "code": code, "alternatives": [],
    }


def get_reservation(db: Session, confirmation_code: str, phone: str) -> Reservation | None:
    phone_norm = normalize_turkish_phone(phone)
    code = confirmation_code.strip().upper()
    return db.execute(
        select(Reservation).where(
            Reservation.confirmation_code == code,
            Reservation.phone == phone_norm,
        )
    ).scalar_one_or_none()


def cancel_reservation(
    db: Session, confirmation_code: str, phone: str
) -> tuple[bool, str | None, Reservation | None]:
    reservation = get_reservation(db, confirmation_code, phone)
    if reservation is None:
        return False, "not_found", None

    if reservation.status == ReservationStatus.CANCELLED:
        return True, None, reservation  # already cancelled: idempotent success

    reservation.status = ReservationStatus.CANCELLED
    db.commit()
    db.refresh(reservation)
    return True, None, reservation
