# ADR-003: bounded free-model failover

Date: 2026-11-23. Scope: WB-12, issue #44. Implementation in progress.

WB-12 requires primary → fallback → manual form without weakening explicit booking
confirmation. The user permits only free models and a monetary budget of $0.
The older WB-06 single-model restriction is amended only for this named free backup.

Use request-local routing in Assistant. Keep Ling 3.2 Flash free as primary and
Gemma 4 26B free as the candidate backup. Do not enable a server fallback until
successful real-free acceptance under the existing data policy. Before every chat, fetch the
official catalog without credentials and verify each configured `:free` ID, zero
prices and `tools`/`tool_choice`. A missing/nonfree primary may be skipped only for
a verified backup. Catalog outage prevents inference. No cross-chat price cache.
Every POST retains zero prompt/completion/request caps, required tools, denied data
collection and disabled provider fallback. Settings reject paid/duplicate IDs;
test-fixture exceptions are restricted to two fixed isolated test model names.

One one-way switch per chat is allowed after timeout/transport failure, HTTP 408,
429 or 5xx, or unusable tool-call responses. One same-model 429 retry respects a
bounded Retry-After of 3–10 seconds. HTTP 400/401/402/403/404 and price/model/size/budget
boundary violations terminate instead. Six total inference HTTP attempts, four
planning rounds, eight MCP tools and 60 seconds include both models and catalog
verification. Other chats start with their own fresh catalog and primary route.

The response exposes sanitized model/outcome metadata, never prompts or credentials.
React displays primary/fallback/unavailable and the required fallback warning.
Both models only use read/propose MCP tools; Booking alone confirms the exact signed
selection after the user's explicit action. Manual booking is independent.

OpenRouter's server-side `models` fallback array was considered. Client-side routing
allows narrower eligible failures and an explicit shared attempt budget; it avoids
switching after authentication, billing or policy errors. A process-global circuit
breaker was deferred: it would couple users and require shared state across replicas.
Free provider capacity and continued availability are not guaranteed.

Verification: deterministic transport unit faults; real MCP/RabbitMQ/PostgreSQL
integration including idempotent concurrent confirmation; desktop/mobile Playwright
fallback and both-model outage/manual recovery; separately labeled genuine free-model
acceptance. Scripted provider tests do not prove actual OpenRouter availability.

Primary sources consulted: [OpenRouter model fallbacks](https://openrouter.ai/docs/guides/routing/model-fallbacks),
[provider routing](https://openrouter.ai/docs/guides/routing/provider-selection),
[current model catalog](https://openrouter.ai/api/v1/models). On 23 November 2026
both configured models were listed with zero prices and required tool parameters.

Actual live checks: Nvidia Nemotron Lightning and Liquid LFM3 returned HTTP404
with "No endpoints found matching your data policy (Free model training)". They
were rejected without relaxing `data_collection=deny` or account privacy settings.
Gemma4 passed catalog/tool checks and reached its provider but returned HTTP429;
successful zero-cost inference is not established. Ling also returned429 in a
current probe; historical WB-06 acceptance remains historical. The local Docker
catalog request returned403, while the host catalog succeeded. These distinct
results are not evidence of working live fallback. Leave deployment disabled and
the PR draft until live acceptance and SSH access are restored.
