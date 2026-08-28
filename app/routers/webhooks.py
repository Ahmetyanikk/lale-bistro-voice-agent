from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import EndOfCallWebhookResponse
from app.services.webhooks import record_end_of_call

router = APIRouter(prefix="/api/webhooks/olovoice")


@router.post("/end-of-call", response_model=EndOfCallWebhookResponse)
def end_of_call(payload: dict = Body(default={}), db: Session = Depends(get_db)):
    # raw dict body on purpose: this must never 422 on an unexpected shape.
    # Analytics-only, no auth check, no signature verification — see
    # app/services/webhooks.py and CLAUDE.md for why.
    duplicate = record_end_of_call(db, payload)
    return EndOfCallWebhookResponse(received=True, duplicate=duplicate)
