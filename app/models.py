import enum
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ReservationStatus(str, enum.Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class RestaurantTable(Base):
    __tablename__ = "tables"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String(10), unique=True)
    capacity: Mapped[int] = mapped_column(Integer)

    reservations: Mapped[list["Reservation"]] = relationship(back_populates="table")


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True)
    tool_call_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    confirmation_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(32))
    party_size: Mapped[int] = mapped_column(Integer)
    table_id: Mapped[int] = mapped_column(ForeignKey("tables.id"))
    # stored as Istanbul-local naive datetimes: single-timezone restaurant,
    # SQLite has no tz-aware column type, conversion happens at the API boundary.
    start_time: Mapped[datetime] = mapped_column(DateTime)
    end_time: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus), default=ReservationStatus.CONFIRMED
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    table: Mapped["RestaurantTable"] = relationship(back_populates="reservations")


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(60))
    price: Mapped[float] = mapped_column()
    description: Mapped[str] = mapped_column(String(300), default="")


class WebhookEvent(Base):
    """End-of-call analytics log. Never touched by reservation logic —
    storing this is the only side effect of the webhook. Analytics-only and
    non-authoritative: nothing here is verified against OloVoice, so no
    privileged action may key off it. See app/services/webhooks.py.

    Deduplicated on the (call_id, idempotency_key) pair. Neither column is
    individually unique — either field alone can legitimately repeat (e.g.
    many unrelated calls with a missing idempotencyKey) — but the pair is
    enforced unique at the DB level as a race backstop behind the
    query-before-insert fast path in app/services/webhooks.py. (SQL NULL
    semantics mean the DB constraint doesn't fire when one of the two
    columns is NULL; the app-level check still catches that case since
    `== None` compiles to `IS NULL`, not `=`.)
    """

    __tablename__ = "webhook_events"
    __table_args__ = (
        UniqueConstraint(
            "call_id", "idempotency_key", name="uq_webhook_event_call_id_idempotency_key"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(100), index=True)
    call_id: Mapped[str | None] = mapped_column(String(100), index=True)
    status: Mapped[str | None] = mapped_column(String(40))
    ended_reason: Mapped[str | None] = mapped_column(String(100))
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)
    analysis_status: Mapped[str | None] = mapped_column(String(40))
    summary: Mapped[str | None] = mapped_column(Text)
    # list of structured-output results with status == "success" only
    structured_outputs: Mapped[list | None] = mapped_column(JSON)
    received_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
