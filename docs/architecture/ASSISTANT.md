# WB-06 Assistant: protocol and operations

Implementation branch: `feat/wb-06-assistant-mcp`, issue [#22](https://github.com/smalvik/biocad-workspace/issues/22).
This document describes source code; current deployment/proof is in CURRENT_STATE and WB-06 change notes.

```mermaid
flowchart LR
  U[Browser: consent and chat] --> A[Assistant FastAPI]
  A --> L[OpenRouter: model tool calls]
  A -->|MCP SDK STDIO| M[MCP child: read/propose only]
  M -->|AMQP request/reply| B[Booking RPC adapter]
  U -->|Explicit exact-slot confirmation| A
  A -->|AMQP authenticated command| B
  B --> H[Same Booking handlers: session, CSRF, validation]
  H --> P[(PostgreSQL: GiST, idempotency, outbox)]
  U -->|Manual form HTTP| H
```

## RabbitMQ contract

The private durable queue `biocad.booking.rpc.v1` accepts JSON envelopes with
`schema_version=1`, UUID `request_id`, absolute Unix `deadline_at`, allowlisted
`operation`, opaque `session_token`, `csrf`, and operation `payload`. The AMQP
`correlation_id` must equal `request_id`; exclusive auto-delete reply queues begin
`biocad.rpc.reply.`. Requests are persistent, TTL 15 s, queue length 256 with
reject-publish overflow, consumer prefetch 4. Client timeout 12 s; server work at
most 10 s and never after its deadline. Replies carry `type=booking.response.v1`,
schema version, correlation, HTTP-compatible status and sanitized domain data.

Operations: auth, authorize (rate window), reserve_llm (spend reservation),
search_employees, list_spaces, get_availability, get_space_details,
create_booking and replay_booking. Unknown envelope fields/operations are rejected.
Read results exclude contact details and other people's raw reservation/session data.
Only fictional colleague profiles are eligible. Distance is measured on the selected
floor to an assignment/reservation for the selected interval, never physical presence.
Lists explicitly report truncation.

The adapter calls the existing FastAPI handlers through **in-process ASGITransport**,
not backend network HTTP. This preserves one set of auth/CSRF/validation/DB/outbox
rules. Internal quota/replay routes additionally require an ASGI extension set only
by this adapter; an HTTP header cannot grant access. Booking remains ready based
on PostgreSQL alone and retries its broker connection in the background. A reply
timeout never authorizes repeating a write with a new idempotency key.

## MCP and LLM boundary

The official pinned `mcp==2.3.0` SDK starts `python -m app.mcp_server` as a real STDIO
subprocess. The SDK client negotiates MCP, discovers schemas, calls tools and reads
typed structured results. No in-process substitute is used in the runtime path.
The child gets only an environment allowlist: Python path/runtime, RabbitMQ URL,
opaque user session, user ID and proposal signing key. It never gets the provider key.

Four required read tools plus `propose_booking` and `ask_clarification` are exposed.
There is **no booking write/cancel tool**. A proposal rechecks real availability,
rejects dedicated/busy/unknown resources, validates aware UTC timestamps and a
future interval within one Moscow calendar day, then signs the exact selection
and owner for 10 minutes. Browser confirmation submits that opaque token and a
stable idempotency key; Booking authenticates and commits using existing rules.
Expired tokens permit only recovery of the same already committed confirmation,
for up to 8 hours, never a new write. Cross-day AI requests ask for one day in this
demo; the independent Booking API remains unchanged.

The OpenRouter key is server-only. The model receives consented user text,
fictional tool data and floor/time context, with at most 6 history messages,
1500 characters per message, 24000 serialized input UTF-8 bytes, 768 output tokens,
4 provider rounds, 8 tool calls and 60 seconds per chat. Two active chats per
Assistant process are allowed. Tool names come from discovery; user-supplied
system/tool history is rejected. Free-form model claims are not confirmation UI:
the server builds proposal/clarification text from actual typed tool results.
Model/provider failure returns an honest error and leaves the manual form usable.

Production uses only `https://openrouter.ai/api/v1`, no redirects/arbitrary base URLs.
Provider routing requires tool parameters, disables provider fallback, denies data
collection and caps prompt/completion pricing at 1/3 USD per million tokens with
zero per-request fee. WB-12 model failover is still separate work.

## Configuration and spend cap

Set server-only `OPENROUTER_API_KEY`, approved `OPENROUTER_PRIMARY_MODEL`, a separate
random `ASSISTANT_PROPOSAL_SECRET` (32+ characters outside local), and an approved
`ASSISTANT_BUDGET_USD`. The default budget is **0**, which prevents inference.
`ASSISTANT_REQUESTS_PER_MINUTE` defaults to 3 per authenticated employee, persisted
in PostgreSQL. `ASSISTANT_BUDGET_EPOCH` identifies a lifetime budget allocation;
**do not change epochs to bypass the cap or reset automatically on deploy/restart**.

Before each provider round Booking atomically reserves 0.05 USD against the shared
epoch cap. This conservatively covers the bounded input/output at the provider
price ceilings; it is not a claim of actual billed cost. Reservation IDs are
idempotent. Uncertain provider outcomes are not refunded. Exhaustion may therefore
stop the demo earlier than its actual billing balance would. Concurrent requests
cannot overspend this reservation cap. Provider account/key limits remain an
additional independent bound, not a replacement for the application cap.

Bootstrap adds a proposal secret to BIOCAD environment secrets while retaining
existing DB/session/broker secrets. No LLM key or spending allowance is inferred
from the existence of credentials. Secrets are never committed or sent to a model.

## Regression versus live proof

`python scripts/check.py --run-type regression` uses a disposable Compose project,
real PostgreSQL/RabbitMQ/STDIO MCP and a **scripted HTTP LLM fixture** from the
existing assistant-tests image. It makes no real inference calls and marks this
in run.json and API/test metadata. The fixture exists only in the test profile,
requires APP_ENV=local, explicit fixture flag, exact local URL/test model/test key,
and is rejected in staging/production. It is never advertised as a real LLM answer.

Live proof is a separate opt-in check against the approved real model and budget,
using fictional users/requests and recording model/tool names, exact selection,
status and cost metadata without API keys, cookies, CSRF or signed proposal tokens.
Published Allure reports must distinguish deterministic regression from live proof.

The prepared proposal-only command is:

```powershell
python scripts/check_live_assistant.py --base-url http://localhost:8080 --expected-model APPROVED_MODEL_ID --allow-paid
```

Run it only after approval and configuring the real local Assistant. It logs in as
fictional e12, tests room capacity / near-Anna / clarification, verifies exact time
and unchanged own bookings, writes sanitized run.json plus `live_llm` Allure results,
then logs out. It never calls booking confirmation/cancellation. Without `--allow-paid`
it exits before network requests. This prepared command is not evidence of execution.

Primary references: [MCP Python SDK client](https://py.sdk.modelcontextprotocol.io/client/),
[MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk),
[aio-pika RPC](https://docs.aio-pika.com/rabbitmq-tutorial/6-rpc.html),
[OpenRouter tool calling](https://openrouter.ai/docs/guides/features/tool-calling),
[provider pricing/routing](https://openrouter.ai/docs/guides/routing/provider-selection).
