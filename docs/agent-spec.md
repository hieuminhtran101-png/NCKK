# AI Agent — Spec & API Contract 📘

**Purpose:** Document the JSON schema, API endpoints, dispatcher behavior, and implementation guidance for the conversational AI Agent that turns Vietnamese user text into structured JSON (intent + entities + confidence) and triggers backend actions (create/query/modify events).

---

## Quick summary ✅

- LLM (3.5–5B) is responsible for converting raw text → JSON structured parse (intent, entities, confidence, raw_text).
- Backend receives JSON at `/agent/interpret` and executes actions by mapping `intent` → handler.
- Confidence threshold default: **0.7** (configurable).
- If `confidence` < threshold, backend returns `needs_clarification` with a follow-up question instead of taking irreversible actions.

---

## JSON schema (from LLM)

Example payload (POST body to `/agent/interpret`):

```json
{
  "intent": "query_events",
  "confidence": 0.94,
  "entities": {
    "date_range": {
      "start": "2026-01-14T00:00:00+07:00",
      "end": "2026-01-14T23:59:59+07:00"
    },
    "event_type": "class",
    "course_name": null
  },
  "raw_text": "Hôm nay tôi có lịch học cái gì?"
}
```

Recommended Pydantic model (informal):

```py
class DateRange(BaseModel):
    start: datetime
    end: datetime

class ParseResult(BaseModel):
    intent: Literal["query_events","create_event","modify_event","query_free_days","delete_event","list_courses"]
    confidence: float
    entities: Dict[str, Any]
    raw_text: str
    # Optionals: date_range could be folded inside entities or as top-level field
```

---

## API Endpoints

1. POST `/agent/interpret` — Accepts JSON parse (from LLM)
   - Request: `ParseResult` JSON
   - Response success example:

```json
{ "ok": true, "action":"query_events", "result": { "events": [...] }, "messages":["Bạn có 2 buổi hôm nay..."] }
```

- Response low-confidence example:

```json
{
  "ok": false,
  "needs_clarification": true,
  "messages": ["Bạn muốn kiểm tra ngày nào? Hôm nay hay ngày khác?"]
}
```

2. POST `/agent/message` — Optional convenience endpoint that accepts raw text and optionally calls LLM internally (useful if backend will sometimes ask LLM instead of client). Example body: `{ "text": "Hôm nay tôi có lịch gì?" }`.

3. WebSocket `/ws/agent/{conversation_id}` — Optional realtime message channel (recommended for fast UX). All messages follow the same JSON shape for agent responses and final action results.

---

## Dispatcher behavior

- Validate incoming JSON (required fields, datetimes parsable).
- If `confidence` < CONFIDENCE_THRESHOLD: return `needs_clarification=true` with follow-up suggestion(s).
- Map `intent` to handler function (e.g., `query_events`, `create_event`, `modify_event`).
- Handlers must:
  - Validate required entities (e.g., `start_time`, `title` for `create_event`)
  - Normalize datetimes to tz-aware ISO
  - Use DB queries (e.g., find events in date_range)
  - Log `AgentActionLog` and the conversation `Message`
- Return human-friendly message(s) in `messages` and structured `result` for client usage.

---

## Security & validation

- Authenticate requests using standard auth (JWT). The agent endpoints must verify `user_id` and associate actions with the authenticated user.
- Sanitize and validate dates, text, and entity fields before acting.
- Rate-limit LLM and agent endpoints to prevent abuse.

---

## Date & time handling

- Use a Vietnamese-aware date resolver for common phrases (e.g., `hôm nay`, `tối nay 19:00`) — `dateparser` or `parsedatetime` with locale support can be used on the client/LLM side, but backend must accept ISO datetimes from LLM.
- Store datetimes as timezone-aware UTC in DB; convert to user timezone on output.

---

## Implementation recommendations (MVP)

- LLM: Call your 3.5–5B model to produce JSON. Keep the model prompt deterministic: include examples (few-shot) to ensure response is JSON-only.
- Backend: FastAPI
  - Use `ParseResult` Pydantic model and a dispatcher module `agent.dispatcher`.
  - For email notifications use MailHog in dev, SMTP for production.
  - Use SQLite for fast dev cycles, PostgreSQL for staging/prod.
  - Use BackgroundTasks for simple reminders; move to Celery+Redis when scaling.
- Frontend: React chat UI with WebSocket client (recommended) or polling fallback.

---

## Tests & validation

- Unit: ParseResult validation, dispatcher routing, handler input validation.
- Integration: mock LLM parse output → POST `/agent/interpret` → assert DB calls and response messages.
- Behavioral: low-confidence payload → returns `needs_clarification` and no DB changes.

---

## Example flows

- Query events ("Hôm nay tôi có lịch học gì?") → LLM returns `query_events` + `date_range` → dispatcher returns events list.
- Create event ("Nhắc tôi học Mạng tối nay 19:00") → LLM returns `create_event` + entities `{title, date_range, remind_before}` → dispatcher validates and creates event.

---

## Next steps (suggested)

1. Confirm `CONFIDENCE_THRESHOLD` (default 0.7).
2. I can create sample FastAPI endpoints + unit tests for `query_events` and `create_event` next.
3. Provide a few Vietnamese prompt examples to lock the LLM few-shot templates.

---

_File created automatically. Update or request edits if you want different organization or additional examples._
