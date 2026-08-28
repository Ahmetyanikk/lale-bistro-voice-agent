# Lale Bistro — backend domain and API

Voice-assistant tool backend for a fictional restaurant. OloVoice owns
voice/STT/TTS/LLM; this service only exposes tool webhooks over HTTP.

## Architecture rules

- **No OloVoice API calls, no frontend.** This phase is backend-only.
- **Domain outcomes vs protocol errors**: business rejections (closed
  Monday, outside opening hours, past time, no table available) return
  HTTP 200 with a `status`/`reason` field — the calling LLM needs a
  structured reason to speak, not an HTTP code to interpret. Only auth
  failures (401) and schema violations (422, e.g. `party_size` outside
  1–8) are real HTTP errors.
- **Timezone**: fixed to `Europe/Istanbul` (`app/timeutil.py`), not
  configurable — this is a single, real-world restaurant, not a
  multi-tenant system. Reservation datetimes are stored as Istanbul-local
  naive `datetime`s in SQLite (no tz-aware column type there); conversion
  to/from aware datetimes happens only at the API boundary
  (`to_naive_istanbul` / `to_aware_istanbul`).
- **Table allocation**: smallest-capacity table that fits the party,
  ties broken by table id (`app/services/availability.py`).
- **Idempotency**: `Reservation.tool_call_id` is unique. Repeating a
  create call with the same `tool_call_id` returns the original
  reservation; it never re-runs allocation.
- **Concurrency**: the check-then-create critical section in
  `create_reservation` is guarded by a process-wide lock
  (`ponytail:` comment in `app/services/reservations.py`) — correct for
  a single-process SQLite demo. Swap for `SELECT ... FOR UPDATE` if this
  ever runs multi-process against Postgres.
- **No queues, no Redis, no microservices, no payments, no SMS, no
  external AI providers.** Anything that looks like one of these outside
  this phase's stated scope is out of bounds; flag it instead of adding it.
- **No Alembic.** SQLite demo uses `Base.metadata.create_all` on startup.

## Project layout

```
app/
  main.py           FastAPI app, lifespan (create tables + seed), /health
  config.py         env-driven settings (TOOL_SECRET, DATABASE_URL)
  database.py       engine/session/Base
  models.py         SQLAlchemy models: RestaurantTable, Reservation, MenuItem
  schemas.py        Pydantic v2 request/response models (strict, extra=forbid)
  security.py       X-Tool-Secret dependency
  seed.py           table + menu seed data
  timeutil.py       Europe/Istanbul helpers
  services/
    availability.py table allocation + opening-hours/overlap logic
    reservations.py reservation domain service (create/get/cancel, idempotency)
    phone.py        Turkish phone -> E.164 normalization
    codes.py        confirmation code generation
    menu.py         menu search
  routers/tools.py   the five POST endpoints
tests/               pytest + FastAPI TestClient, in-memory SQLite per test
```

## Test commands

```
pip install -e ".[dev]"
pytest
```

Run a single file: `pytest tests/test_reservations.py -v`
