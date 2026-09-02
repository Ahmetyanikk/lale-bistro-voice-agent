# Lale Bistro — Voice Assistant Backend

Backend domain and tool API for a Turkish restaurant voice assistant
(OloVoice). This phase implements table availability, reservation
create/get/cancel, and menu search as webhook-style tool endpoints.
OloVoice itself is not called from here, and there is no frontend.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e ".[dev]"
copy .env.example .env          # then edit TOOL_SECRET
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Run tests:

```bash
pytest
```

## Configuration

| Variable                    | Required | Default                    | Read by                          |
|------------------------------|----------|-----------------------------|-----------------------------------|
| `TOOL_SECRET`                | yes      | —                            | this backend (`app/config.py`)   |
| `OLOVOICE_TOOL_TOKEN`        | no       | —                            | temporary saved-tool URL fallback |
| `DATABASE_URL`               | no       | `sqlite:///./lale_bistro.db` | this backend                     |
| `OLOVOICE_API_KEY`           | no       | —                            | not used yet (see below)         |
| `BASE_URL`                   | no       | —                            | `scripts/smoke_test.py`, dashboard setup |
| `OLOVOICE_ASSISTANT_ID`      | no       | —                            | not used yet (dashboard setup)   |
| `OLOVOICE_PHONE_NUMBER_ID`   | no       | —                            | not used yet (dashboard setup)   |
| `OLOVOICE_ORGANIZATION_ID`   | no       | —                            | not used yet (dashboard setup)   |

**`TOOL_SECRET` vs `OLOVOICE_API_KEY` — these authenticate opposite
directions and must never be the same value:**
- `TOOL_SECRET` authenticates **OloVoice calling us** — normally every
  `/api/tools/*` request carries header `X-Tool-Secret: <TOOL_SECRET>`.
- If the OloVoice saved-tool dashboard does not expose custom headers, set a
  separate short-lived `OLOVOICE_TOOL_TOKEN` and append
  `?tool_token=<OLOVOICE_TOOL_TOKEN>` to each saved tool's webhook URL. This
  fallback is disabled when the variable is unset. Query strings may appear in
  private infrastructure logs, so never reuse `TOOL_SECRET` here and rotate the
  token after the demo.
  `/health` and the end-of-call webhook do not require it.
- `OLOVOICE_API_KEY` would authenticate **our code calling OloVoice's own
  API** (e.g. to create/update the assistant programmatically). Nothing in
  this repo does that yet — Phase 2 only prepares the dashboard config
  assets under `olovoice/`; assistant setup is done manually in the
  OloVoice dashboard (see `olovoice/dashboard-setup.md`) to keep live-demo
  risk low.

## Docker

```bash
docker build -t lale-bistro .
docker run -p 8000:8000 -e TOOL_SECRET=changeme lale-bistro
```

## curl examples

```bash
SECRET=changeme-local-dev-secret

curl -s http://localhost:8000/health

curl -s -X POST http://localhost:8000/api/tools/check-availability \
  -H "X-Tool-Secret: $SECRET" -H "Content-Type: application/json" \
  -d '{"tool_call_id":"call-1","party_size":4,"requested_time":"2026-09-01T19:30:00"}'

curl -s -X POST http://localhost:8000/api/tools/create-reservation \
  -H "X-Tool-Secret: $SECRET" -H "Content-Type: application/json" \
  -d '{"tool_call_id":"call-2","customer_name":"Ayse Yilmaz","phone":"0532 123 45 67","party_size":4,"requested_time":"2026-09-01T19:30:00"}'

curl -s -X POST http://localhost:8000/api/tools/get-reservation \
  -H "X-Tool-Secret: $SECRET" -H "Content-Type: application/json" \
  -d '{"tool_call_id":"call-3","confirmation_code":"7K2Q","phone":"0532 123 45 67"}'

curl -s -X POST http://localhost:8000/api/tools/cancel-reservation \
  -H "X-Tool-Secret: $SECRET" -H "Content-Type: application/json" \
  -d '{"tool_call_id":"call-4","confirmation_code":"7K2Q","phone":"0532 123 45 67"}'

curl -s -X POST http://localhost:8000/api/tools/search-menu \
  -H "X-Tool-Secret: $SECRET" -H "Content-Type: application/json" \
  -d '{"tool_call_id":"call-5","query":"kebap"}'
```

## OloVoice integration assets (Phase 2)

`olovoice/` contains everything needed to wire this backend into an OloVoice
inbound voice assistant, manually through the OloVoice dashboard:

- `system_prompt.md` — full Turkish system prompt for the assistant.
- `knowledge_base.md` — static restaurant facts (hours, policy, menu) that
  match this backend's seed data. Dynamic availability is never duplicated
  here — it's always a live `check_availability` call.
- `menu_facts.json` — machine-readable counterpart of the knowledge base's
  menu table and vegetarian list; `tests/test_menu_facts.py` checks it
  against `app/seed.py` directly instead of parsing the markdown prose.
- `tools.json` — 5 saved-tool definitions (one per `/api/tools/*` endpoint).
  `inputSchema.properties` are derived directly from the Pydantic request
  models in `app/schemas.py` — verified by `tests/test_olovoice_assets.py`.
  OloVoice's own tool-config wrapper keys (`webhookUrl`, `includeMetadata`,
  `metadataKey`, `timeoutSec`, `speakResult`) are camelCase per OloVoice's
  convention; the business arguments inside `inputSchema.properties` stay
  snake_case (`party_size`, `requested_time`, …) because they must match
  `app/schemas.py` byte-for-byte — that backend uses `extra="forbid"`, so a
  camelCase body would 422. `tool_call_id` and `call_context` are injected
  by OloVoice itself (the model never generates either), so neither
  appears in any `inputSchema` even though every endpoint accepts both.
- `structured_output.json` — per-call structured extraction schema for
  analytics.
- `dashboard-setup.md` — exact manual dashboard steps.

No frontend and no OloVoice API calls are implemented yet; dashboard
configuration is manual by design.

### End-of-call webhook

`POST /api/webhooks/olovoice/end-of-call` accepts OloVoice's documented
end-of-call-report shape and follows its field paths exactly:
`message.idempotencyKey`, `message.endedReason`, `message.call.id`,
`message.call.status`, `message.call.startedAt`/`endedAt`,
`message.analysis.summary`, `message.analysisStatus`. It stores only those
fields plus successful structured outputs (from
`message.call.structuredOutputs`, falling back to
`message.structuredOutputs`; entries other than `status == "success"` are
dropped, `null` becomes `[]`) — never phone numbers or secrets — and never
triggers reservation logic. Deduplication is on the `(call.id,
idempotencyKey)` pair. It parses the body as a raw dict and degrades every
field defensively instead of rejecting malformed shapes, since the payload
comes from a platform we don't control.

This endpoint is **analytics-only and non-authoritative**: it has no auth
check and no signature verification, because OloVoice's documentation does
not define a webhook signature scheme — none is invented here. Before any
production side effect is ever driven by this webhook, `message.call.id`
must first be re-verified against OloVoice's own Call Logs API.

### Smoke test

```bash
BASE_URL=https://your-domain TOOL_SECRET=... python scripts/smoke_test.py
```

Checks `/health`, one `check-availability` call, and one `search-menu`
call. Stdlib only — no project install required to run it against a
deployed instance. Never prints the secret.

## Notes

- `requested_time` without a UTC offset is interpreted as Europe/Istanbul
  local time; with an offset, it's converted to Istanbul time.
- Business-rule rejections (closed Monday, outside 12:00–23:00, past
  time, table unavailable) come back as HTTP 200 with `reason` set —
  only auth failures and malformed requests are HTTP errors.
- See `CLAUDE.md` for architecture rules.
