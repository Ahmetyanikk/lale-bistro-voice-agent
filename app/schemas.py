from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ToolRequestBase(BaseModel):
    # forbid extra: only OloVoice's own injected fields (tool_call_id,
    # call_context) and each tool's declared business fields are allowed —
    # anything else is a genuinely unknown field and still 422s.
    # (not model-level strict=True: JSON has no datetime type, and strict
    # mode rejects the ISO8601 strings that requests actually send.)
    model_config = ConfigDict(extra="forbid")

    tool_call_id: str = Field(min_length=1, max_length=100)
    # added by OloVoice when includeMetadata=true; the model never generates
    # this, so it's excluded from every tool's inputSchema in tools.json.
    call_context: dict[str, Any] | None = None


class CheckAvailabilityRequest(ToolRequestBase):
    party_size: int = Field(ge=1, le=8)
    requested_time: datetime


class CreateReservationRequest(ToolRequestBase):
    customer_name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=5, max_length=32)
    party_size: int = Field(ge=1, le=8)
    requested_time: datetime


class GetReservationRequest(ToolRequestBase):
    confirmation_code: str = Field(min_length=1, max_length=20)
    phone: str = Field(min_length=5, max_length=32)


class CancelReservationRequest(ToolRequestBase):
    confirmation_code: str = Field(min_length=1, max_length=20)
    phone: str = Field(min_length=5, max_length=32)


class SearchMenuRequest(ToolRequestBase):
    query: str | None = Field(default=None, max_length=100)
    category: str | None = Field(default=None, max_length=60)


class CheckAvailabilityResponse(BaseModel):
    tool_call_id: str
    available: bool
    table_label: str | None = None
    party_size: int
    requested_time: datetime
    reason: str | None = None
    alternatives: list[datetime] = []


class CreateReservationResponse(BaseModel):
    tool_call_id: str
    status: str
    confirmation_code: str | None = None
    table_label: str | None = None
    party_size: int
    start_time: datetime | None = None
    end_time: datetime | None = None
    reason: str | None = None
    alternatives: list[datetime] = []


class GetReservationResponse(BaseModel):
    tool_call_id: str
    found: bool
    confirmation_code: str | None = None
    status: str | None = None
    customer_name: str | None = None
    phone: str | None = None
    party_size: int | None = None
    table_label: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None


class CancelReservationResponse(BaseModel):
    tool_call_id: str
    cancelled: bool
    confirmation_code: str
    reason: str | None = None


class MenuItemOut(BaseModel):
    name: str
    category: str
    price: float
    description: str


class SearchMenuResponse(BaseModel):
    tool_call_id: str
    count: int
    items: list[MenuItemOut]


class EndOfCallWebhookResponse(BaseModel):
    received: bool
    duplicate: bool
