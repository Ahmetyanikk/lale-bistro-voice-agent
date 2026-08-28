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
- **Naming domains don't mix.** Three separate conventions coexist on
  purpose: OloVoice's own tool-config wrapper keys are camelCase
  (`webhookUrl`, `includeMetadata`, …); the JSON body fields inside
  `inputSchema.properties` stay snake_case because they must exactly match
  `app/schemas.py` (`extra="forbid"` — a camelCase body would 422);
  `structured_output.json` analytics fields are snake_case per the spec
  that defined them. Don't "fix" any of these to match the others.
- **`tool_call_id` and `call_context` are injected by OloVoice, not
  model-generated.** Every request model inherits both from
  `ToolRequestBase` (`app/schemas.py`) so they're always accepted
  regardless of which tool is called, but neither appears in any tool's
  `inputSchema.properties` in `olovoice/tools.json` — the model never
  produces them, so the schema the model sees shouldn't ask for them.
  `extra="forbid"` still 422s on anything genuinely unrecognized.
- **The end-of-call webhook is analytics-only and non-authoritative.** It
  only writes a `WebhookEvent` log row (call id, status, ended reason,
  timestamps, analysis status, summary, successful structured outputs —
  never phone numbers) and never mutates reservation state. It parses the
  body as a raw `dict`, not a strict Pydantic model, so a
  malformed/unexpected shape from OloVoice degrades a field to `None`
  instead of ever 422/500ing. Field mapping follows OloVoice's documented
  `message.*` paths exactly (see `app/services/webhooks.py` docstring) —
  `idempotencyKey` and `endedReason` live on `message`, not
  `message.call`. Dedup key is the `(message.call.id,
  message.idempotencyKey)` pair, checked at the application level (not a
  DB unique constraint), since either half can legitimately repeat alone.
  Structured outputs are read from `message.call.structuredOutputs`
  (preferred) or `message.structuredOutputs` (fallback), never
  `analysis.structuredData`, and only entries with `status == "success"`
  are kept; `null` becomes `[]`.
  There is **no auth check and no signature verification** on this
  endpoint — OloVoice's docs don't define a webhook signature scheme, so
  none is assumed or invented here. This is intentional, not a gap to
  "fix" with an invented HMAC scheme. Before any production side effect
  (e.g. touching a reservation, alerting a human) is ever driven by this
  webhook, the code must first re-verify `message.call.id` against
  OloVoice's own Call Logs API — never act on webhook content directly.
- **OloVoice API calls are not implemented.** `OLOVOICE_API_KEY` is
  reserved in `.env.example` for a future phase; dashboard setup
  (`olovoice/dashboard-setup.md`) is manual by design to reduce live-demo
  risk.

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
  routers/
    tools.py          the five POST /api/tools/* endpoints
    webhooks.py        POST /api/webhooks/olovoice/end-of-call
tests/                pytest + FastAPI TestClient, in-memory SQLite per test
olovoice/             OloVoice dashboard config assets (prompt, KB, tool defs,
                      structured output schema, manual setup steps)
scripts/smoke_test.py stdlib-only post-deploy check
```

## Test commands

```
pip install -e ".[dev]"
pytest
```

Run a single file: `pytest tests/test_reservations.py -v`
