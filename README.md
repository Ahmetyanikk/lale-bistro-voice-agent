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

| Variable       | Required | Default                        |
|----------------|----------|---------------------------------|
| `TOOL_SECRET`  | yes      | —                                |
| `DATABASE_URL` | no       | `sqlite:///./lale_bistro.db`     |

Every `/api/tools/*` endpoint requires header `X-Tool-Secret: <TOOL_SECRET>`.
`/health` does not.

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
  -d '{"tool_call_id":"call-3","confirmation_code":"LBL-7K2Q","phone":"0532 123 45 67"}'

curl -s -X POST http://localhost:8000/api/tools/cancel-reservation \
  -H "X-Tool-Secret: $SECRET" -H "Content-Type: application/json" \
  -d '{"tool_call_id":"call-4","confirmation_code":"LBL-7K2Q","phone":"0532 123 45 67"}'

curl -s -X POST http://localhost:8000/api/tools/search-menu \
  -H "X-Tool-Secret: $SECRET" -H "Content-Type: application/json" \
  -d '{"tool_call_id":"call-5","query":"kebap"}'
```

## Notes

- `requested_time` without a UTC offset is interpreted as Europe/Istanbul
  local time; with an offset, it's converted to Istanbul time.
- Business-rule rejections (closed Monday, outside 12:00–23:00, past
  time, table unavailable) come back as HTTP 200 with `reason` set —
  only auth failures and malformed requests are HTTP errors.
- See `CLAUDE.md` for architecture rules.
