# OloVoice Dashboard Setup — Lale Bistro Reservation Assistant

Manual dashboard steps for wiring this backend to an OloVoice inbound voice
assistant. No API automation is done in this phase — everything below is a
click-through in the OloVoice web dashboard, done manually to keep live-demo
risk low.

Anything in `[FROM DASHBOARD: ...]` is a value **you must copy from your own
OloVoice account** — never guess or invent an ID, model name, or voice name.

## Prerequisites

- Backend deployed and reachable at a public HTTPS URL (`BASE_URL` in
  `.env.example`). OloVoice will not call a plain-HTTP or localhost URL.
- A `TOOL_SECRET` value generated for this deployment (not the repo default).
- `olovoice/tools.json`, `olovoice/structured_output.json`,
  `olovoice/system_prompt.md`, `olovoice/knowledge_base.md` open/ready to
  copy from.

## 1. Create the assistant

1. In the OloVoice dashboard, create a new **Assistant**.
2. Name it "Lale Bistro Rezervasyon Asistanı".
3. Paste the full contents of `olovoice/system_prompt.md` into the
   assistant's system prompt field.

## 2. Select Turkish STT

1. Open the assistant's **Speech-to-Text** (transcriber) settings.
2. Choose a provider/model that supports Turkish (`tr` / `tr-TR`).
   `[FROM DASHBOARD: exact STT provider and model name available on your
   account — pick the one whose language list includes Turkish.]`
3. Set the language explicitly to Turkish if the provider requires it.

## 3. Select an economical, low-latency LLM

1. Open the assistant's **Model** settings.
2. Pick the smallest/cheapest model tier your OloVoice account offers that
   still reliably follows multi-step tool-calling instructions.
   `[FROM DASHBOARD: exact model name/tier list — this varies by account
   and changes over time, do not hardcode one.]`
3. Keep temperature low (deterministic tool-calling matters more here than
   creative variety).

## 4. Select and test a Turkish TTS voice

1. Open **Text-to-Speech** (voice) settings.
2. Filter by Turkish voices. `[FROM DASHBOARD: exact voice name/id list for
   Turkish available on your account.]`
3. Use the dashboard's built-in "preview/test voice" button with a short
   Turkish sentence (e.g. "İyi günler, Lale Bistro'ya hoş geldiniz.") to
   confirm pronunciation quality before saving.

## 5. Attach the knowledge base

1. Open the assistant's **Knowledge Base** section.
2. Upload or paste `olovoice/knowledge_base.md`.
3. Attach it to this assistant.

## 6. Create and attach the saved tools

For each of the 5 objects in `olovoice/tools.json`:

1. Go to **Tools → Create new tool** (or "saved tool"/"function").
2. Set the fields from the JSON object exactly:
   - `name`
   - `description`
   - `webhookUrl` — replace `https://YOUR_PUBLIC_DOMAIN` with your real
     `BASE_URL` (must stay HTTPS).
   - `method`: POST
   - `inputSchema`: paste as-is (JSON Schema, `additionalProperties: false`)
   - `includeMetadata`: true
   - `metadataKey`: `call_context`
   - `timeoutSec`: 5
   - `speakResult`: false
3. Save the tool, then attach it to the assistant.
4. Repeat for all 5 tools: `check_availability`, `create_reservation`,
   `get_reservation`, `cancel_reservation`, `search_menu`.

**Naming note:** the fields above (`webhookUrl`, `includeMetadata`,
`metadataKey`, `timeoutSec`, `speakResult`) are camelCase because that's
OloVoice's own tool-config convention — leave them as-is. The properties
*inside* `inputSchema` (`party_size`, `requested_time`, …) are snake_case
on purpose: they must match this backend's request fields exactly. Don't
"fix" either to match the other.

**`tool_call_id` and `call_context` are not in `inputSchema` on purpose.**
OloVoice adds `tool_call_id` to every tool call automatically, and adds
`call_context` when `includeMetadata: true` is set (which it is, above).
Neither is something the model generates, so neither belongs in the
schema the model sees — but the backend accepts both on every endpoint.
Nothing to configure here beyond setting `includeMetadata: true` and
`metadataKey: call_context` as shown.

## 7. Add the X-Tool-Secret header

For **each** of the 5 tools, in its request headers section, add:

```
X-Tool-Secret: <your real TOOL_SECRET value>
```

Replace the `REPLACE_WITH_TOOL_SECRET` placeholder from `tools.json` with
the actual secret configured on your backend deployment. Never commit this
real value to the repository — it only lives in the OloVoice dashboard and
your deployment's environment variables.

If the saved-tool dashboard editor does not expose custom request headers,
use the explicit demo fallback instead:

1. Generate a separate random value and configure it on the backend as
   `OLOVOICE_TOOL_TOKEN`. Do not reuse `TOOL_SECRET`.
2. Append `?tool_token=<OLOVOICE_TOOL_TOKEN>` to each saved tool's
   `webhookUrl`.
3. Rotate or remove `OLOVOICE_TOOL_TOKEN` after the demo. The fallback is
   disabled whenever that environment variable is absent. Query strings can
   appear in private infrastructure logs, which is why this is a short-lived
   compatibility fallback rather than the preferred production mechanism.

## 8. Add structured output

1. Open the assistant's **Structured Output** (or "Analysis Schema")
   settings.
2. Paste the contents of `olovoice/structured_output.json`.
3. Save.

## 9. Connect the assigned inbound phone number

1. Go to **Phone Numbers** in the dashboard.
2. Either provision a new number or use one already assigned to your
   account. `[FROM DASHBOARD: the actual phone number / phone number ID
   available on your account — this is assigned by OloVoice, not chosen by
   you here.]`
3. Assign that phone number to the "Lale Bistro Rezervasyon Asistanı"
   assistant.

## 10. Publish and activate the assistant

1. Review all sections above (prompt, STT, LLM, TTS, knowledge base, tools,
   structured output, phone number).
2. Click **Publish** / **Activate** (exact label depends on your dashboard
   version).
3. Confirm the assistant status shows as active/live.

## 11. Run a browser test

1. Use the dashboard's built-in **Web/Browser Test Call** feature (usually
   a "Test" or "Talk to assistant" button on the assistant page).
2. Run through one full happy-path scenario: ask for a table, give a date,
   time, party size, name, and phone, confirm, and check that a
   confirmation code comes back.
3. Watch the live transcript panel to confirm tool calls are firing with
   the right arguments.

## 12. Run a real phone test

1. Call the assigned inbound number from an actual phone.
2. Repeat the happy-path scenario, plus at least one edge case (e.g. ask
   for a Monday, or a party of 10) to confirm the assistant follows the
   human-follow-up and closed-day rules from the system prompt.

## 13. Inspect call logs

1. Open **Call Logs** / **History** for the assistant.
2. Open the call you just made and confirm:
   - Transcript matches what was said.
   - Tool call entries show the exact request/response JSON sent to
     `BASE_URL/api/tools/...`.
   - Structured output fields were populated per
     `olovoice/structured_output.json`.
   - The end-of-call webhook fired (cross-check against your backend's
     stored `WebhookEvent` rows for that call's `idempotencyKey` and
     `call.id`).

**About the end-of-call webhook:** it is analytics-only and
non-authoritative. There's no signature header to configure here because
OloVoice's documentation doesn't define one for this webhook — the
backend doesn't invent one either. It only logs call metadata; it never
creates, cancels, or otherwise touches a reservation. If a future phase
needs the webhook to trigger a real (privileged) action, that code must
first re-fetch and verify the call by `call.id` through OloVoice's Call
Logs API before acting — never act on the webhook body directly.
