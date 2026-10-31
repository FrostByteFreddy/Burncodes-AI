# Chat answers

Flow: widget/chat page (`frontend/src/components/chat/BaseChat.vue`) →
`POST /api/chat/<tenant>` (checks: chatbot on, password unlocked or owner,
owner balance > 0) → `chat_task` on worker_chat → the page long-polls
`GET /api/chat/task/<id>/status`.

## What the model gets (`services/worker_chat/app/chat/tasks.py`, `chat_task`)

The system instruction is built in this order:

1. **Persona + template + fine-tune rules** (`_build_system_instruction`) from
   the chatbot's settings (legacy `{context}`/`{input}` slots stripped).
2. **Now** (`_now_context`): weekday, date, time, time zone (`APP_TIMEZONE`),
   with the rule "next Tuesday / tomorrow only within 7 days".
3. **Verified dates** (`_dates_context`): from `tenant_events`. Series with
   future dates first, soonest first, the ones the question names before all
   others (`names.mentioned`, typos included); past series fill the rest so the
   model says "no future dates" instead of guessing; max 40 series, 4 dates
   each. Names differing only in punctuation are one series. With calendar
   feeds on, each series carries a `{calendar: KEY}` the model turns into
   `[[calendar:KEY]]`.
4. **Contact card** (`knowledge/contact.contact_context`).
5. **Name hint** (`_name_hint`): if the question misspells an event or page
   title (`knowledge/names.py`, letter-triple index, 5–20 ms on 1000 names):
   "they most likely mean «…»".
6. **Facts** (`knowledge/facts.relevant_facts`): learned values whose label
   matches the question's word stems (and the previous question's).
7. **Rules**: sources, unknown answers, chat style, and last the language rule.

Contents: the last `CHAT_HISTORY_TURNS` exchanges from `chat_logs` (never from
the client), then the question plus `_LANGUAGE_NOTE` ("answer in the language
of my message") as a second part; the note is not stored.

Tools: `file_search` on the chatbot's store, if it has one.

## After the answer

- `_keep_known_links`: links to pages we don't know become plain text.
- `_drop_stray_calendars`: calendar markers for series not given.
- `_inline_sources` / `_ensure_source`: source chips after the lines they back,
  from File Search grounding metadata (`source_url`), verified dates' and
  facts' pages, else one line at the end.
- Billing: `billable_tokens(usage)` (includes File Search context and
  thinking) × `RATES["chat"]` → `charge(kind="answer")`; logged to `chat_logs`.

Frontend rendering: `frontend/src/utils/chatProcessor.js` (marked + DOMPurify),
source chips and `[[calendar:…]]` buttons in `BaseChat.vue`.

## Testing answers

Run the real task in the local chat container (same database and Gemini as
production; `None` as user id = not billed; it still lands in `chat_logs`):

```sh
docker cp backend/services/worker_chat/app/chat/tasks.py swiftanswer-local-celery_worker_chat-1:/app/app/chat/tasks.py
docker exec -e PYTHONPATH=/app -w /app swiftanswer-local-celery_worker_chat-1 python -c "
import uuid; from app.chat.tasks import chat_task
print(chat_task.run('<tenant-id>', 'Wann ist …?', [], str(uuid.uuid4()), None)['answer'])"
```

Then build the chat image the way production does (SKILL.md rule 1). Unit
tests for the prompt parts: `tests/test_knowledge.py` (`TestChatDates`,
`TestChatDateSelection`, `TestSystemInstruction`), `tests/test_names.py`.
