# WB-10 — local reproducibility and delivery evidence

Issue [#38](https://github.com/smalvik/biocad-workspace/issues/38), branch
`docs/wb-10-delivery-evidence` from develop05e08e6; WB-08 final notes carried as e301cb3.
The implementation changes Markdown only, with no runtime/schema/API/frontend-flow change.

## Actual fresh local launch

`python artifacts/run_logged.py artifacts/WB-10-local-docs.log python artifacts/wb10_local_docs.py`
executes the README Compose command shape with a unique `-p biocad-wb10-docs-30b665ee95`
and free loopback ports instead of occupying existing localhost development ports.
`docker compose --env-file .env.example -f infra/compose.yaml up -d --build --wait`
really builds/starts **7 services, all healthy**; no private `.env` or external LLM is used.
The existing two read-only map/employee scenarios run on desktop/mobile: **4 PASS**.
Tests use the immutable v1.4.1 E2E image (source5364c9e); the launched app is built
from base **e301cb3291ea86e6aab669b56d8bed8a7842c0fe**, tree **dirty** (documentation changes).
The test project and only its own volumes/network are removed, cleanup exit0.
[Run metadata](../../artifacts/biocad-wb10-docs-30b665ee95/run.json),
[actual log](../../artifacts/WB-10-local-docs.log),
[actual Allure smoke](../../artifacts/biocad-wb10-docs-30b665ee95/allure-results).

## Architecture and static checks

Real Mermaid parse and Chromium SVG rendering, tooling version11.4.1:
**3 PASS**, C1 **7 nodes**, C2 **15**, Assistant **7**. Inspected C2 screenshot and
shortened two wrapping cluster headings, then rendered the final diagrams again.
[Tool result](../../artifacts/WB-10-mermaid/run.json),
[C1 SVG](../../artifacts/WB-10-mermaid/C1.svg), [C2 SVG](../../artifacts/WB-10-mermaid/C2.svg).
Relative Markdown/code links and configured-secret checks are run against staged files;
policy checks use the actual WB-10 branch and Conventional Commit title.
No unit tests mirroring prose or new product browser flow tests were added.
README states active hours are unmeasured; user was asked, no numbers are invented.
The AI-LOG distinguishes user decisions, agent implementation and explicit agent self-review.

## Complete real-service regression before PR

`python artifacts/run_logged.py artifacts/WB-10-regression.log python scripts/check.py --run-type regression`
**PASS**, run **20261116T012006Z-46c1a7**, base **e301cb3291ea86e6aab669b56d8bed8a7842c0fe**, tree **dirty**:
**248 checks**, **35 commands exit0**, **222 raw Allure** + **26 Vitest separately**.
111 Booking/delivery +24 Assistant +20 Worker +2 persistence +5 recovery phases
+26 Vitest +60 desktop/mobile Playwright. True child RED 2 failed / restored GREEN
3 passed remain attachments of the outer sensitivity gate, not extra headline checks.
PostgreSQL/RabbitMQ/MCP/Mailpit real; LLM provider explicitly scripted, no inference calls.
[Metadata](../../artifacts/20261116T012006Z-46c1a7/run.json),
[actual full log](../../artifacts/WB-10-regression.log).

## Remote gates

PR, post-merge regression/server/staging and main/release remain pending until actual
completion. Current published/deployed product is still v1.4.1, not an anticipated version.
Initial server-only data snapshot retains **7 bookings /12 accounts per environment**;
individual IDs/fingerprints remain root-only on the server. **23 unrelated containers**
recorded before delivery. [Aggregate counts](../../artifacts/WB-10-data-before.json).
Final release, preservation and public checks will be recorded after they occur.
