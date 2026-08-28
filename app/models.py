import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
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
