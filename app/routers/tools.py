from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    CancelReservationRequest,
    CancelReservationResponse,
    CheckAvailabilityRequest,
    CheckAvailabilityResponse,
    CreateReservationRequest,
    CreateReservationResponse,
    GetReservationRequest,
    GetReservationResponse,
    MenuItemOut,
    SearchMenuRequest,
    SearchMenuResponse,
)
from app.security import require_tool_secret
from app.services import menu, reservations
from app.services.codes import normalize_confirmation_code
from app.timeutil import to_aware_istanbul, to_naive_istanbul

router = APIRouter(prefix="/api/tools", dependencies=[Depends(require_tool_secret)])


@router.post("/check-availability", response_model=CheckAvailabilityResponse)
def check_availability(payload: CheckAvailabilityRequest, db: Session = Depends(get_db)):
    result = reservations.check_availability(db, payload.party_size, payload.requested_time)
    table = result["table"]
    return CheckAvailabilityResponse(
        tool_call_id=payload.tool_call_id,
        available=result["available"],
        table_label=table.label if table else None,
        party_size=payload.party_size,
        requested_time=to_aware_istanbul(to_naive_istanbul(payload.requested_time)),
        reason=result["reason"],
        alternatives=[to_aware_istanbul(a) for a in result["alternatives"]],
    )


@router.post("/create-reservation", response_model=CreateReservationResponse)
def create_reservation(payload: CreateReservationRequest, db: Session = Depends(get_db)):
    result = reservations.create_reservation(
        db,
        payload.tool_call_id,
        payload.customer_name,
        payload.phone,
        payload.party_size,
        payload.requested_time,
    )
    table = result["table"]
    return CreateReservationResponse(
        tool_call_id=payload.tool_call_id,
        status=result["status"],
        confirmation_code=result["code"],
        table_label=table.label if table else None,
        party_size=payload.party_size,
        start_time=to_aware_istanbul(result["start"]) if result["start"] else None,
        end_time=to_aware_istanbul(result["end"]) if result["end"] else None,
        reason=result["reason"],
        alternatives=[to_aware_istanbul(a) for a in result["alternatives"]],
    )


@router.post("/get-reservation", response_model=GetReservationResponse)
def get_reservation(payload: GetReservationRequest, db: Session = Depends(get_db)):
    reservation = reservations.get_reservation(db, payload.confirmation_code, payload.phone)
    if reservation is None:
        return GetReservationResponse(tool_call_id=payload.tool_call_id, found=False)
    return GetReservationResponse(
        tool_call_id=payload.tool_call_id,
        found=True,
        confirmation_code=normalize_confirmation_code(reservation.confirmation_code),
        status=reservation.status.value,
        customer_name=reservation.customer_name,
        phone=reservation.phone,
        party_size=reservation.party_size,
        table_label=reservation.table.label,
        start_time=to_aware_istanbul(reservation.start_time),
        end_time=to_aware_istanbul(reservation.end_time),
    )


@router.post("/cancel-reservation", response_model=CancelReservationResponse)
def cancel_reservation(payload: CancelReservationRequest, db: Session = Depends(get_db)):
    cancelled, reason, reservation = reservations.cancel_reservation(
        db, payload.confirmation_code, payload.phone
    )
    code = (
        normalize_confirmation_code(reservation.confirmation_code)
        if reservation
        else normalize_confirmation_code(payload.confirmation_code)
    )
    return CancelReservationResponse(
        tool_call_id=payload.tool_call_id,
        cancelled=cancelled,
        confirmation_code=code,
        reason=reason,
    )


@router.post("/search-menu", response_model=SearchMenuResponse)
def search_menu(payload: SearchMenuRequest, db: Session = Depends(get_db)):
    items = menu.search_menu(db, payload.query, payload.category)
    return SearchMenuResponse(
        tool_call_id=payload.tool_call_id,
        count=len(items),
        items=[
            MenuItemOut(name=i.name, category=i.category, price=i.price, description=i.description)
            for i in items
        ],
    )
