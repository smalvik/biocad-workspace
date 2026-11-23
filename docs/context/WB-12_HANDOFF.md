# WB-12 continuation — 23 November 2026 Moscow

User requested continuation, not a pause. Issue [#44](https://github.com/smalvik/biocad-workspace/issues/44),
branch `feat/wb-12-llm-failover`, draft [PR #45](https://github.com/smalvik/biocad-workspace/pull/45)
into develop. Implementation commit `19313a415a9ae8a3665c97ad7d98d6daee52da33`;
following documentation commit records the created PR. Start from this branch,
inspect Git status and exact [PR checks](https://github.com/smalvik/biocad-workspace/pull/45/checks).
Do not duplicate the issue/branch/PR. No merge, server change or new release claimed.

Implemented: Assistant bounded request-local primary→free fallback, current catalog
price/tool verification, per-request zero caps, one switch/six inference attempts,
4 rounds/8 tools/60 seconds including catalog, no switching after auth/billing/policy
or price/model boundaries. React primary/fallback/unavailable warning and manual flow.
No DB migration. [ADR-003](../adr/003-free-model-failover.md), [actual evidence](../evidence/WB-12-local.md).

Local full regression **277 passed /35 commands exit0 /251 raw Allure +26 Vitest**,
run `20261123T075832Z-5fd8c1`, base1219797/dirty; exact committed-tree CI is separate.
Latest focused43 unit/Ruff passed after candidate selection. Deterministic provider,
real PostgreSQL/RabbitMQ/STDIO MCP. Real-free acceptance **not passed**:
isolated Docker catalog403 → API/desktop/mobile503 before inference; test project
and volumes removed. Host Nvidia/Liquid policy404, Ling429, Gemma4 26B429.
No successful cost0 response was obtained; keep fallback empty until acceptance.
No paid route/credits/training-policy relaxation. `usage.cost=0` from historical
v1.3.0 is not current-model proof. Logs and failed artifacts remain ignored locally.

Blockers and next actions:

1. Restore administrator SSH22 connectivity; Windows and Docker both time out,
   HTTPS443 connects. Previous VPN interface10.8.1.2/index73 is absent; user was
   asked asynchronously to enable it or supply new SSH details. Existing pinned
   host keys/admin key in ignored env remain; never print/copy credentials.
   `artifacts/server_ops.py` supports the existing transport. Its old VPN wrapper
   has stale hardcoded interface information: inspect current interfaces first.
2. Obtain successful real-free backup acceptance under unchanged privacy/cost caps.
   Candidate `google/gemma-4-26b-a4b-it:free`; current catalog zero/tool flags alone
   do not prove live availability. Avoid unbounded probes or paid alternatives.
   Distinguish scripted primary failure from actual backup response in reports.
3. Inspect exact-head CI/review. Keep PR draft while the above is unresolved.
   Review is agent self-review, not independent human approval. Production stays
   **v1.4.3 / mainfb0d342**, develop9c30d7a; no next-task branch before WB-12 disposition.
4. Before eventually merging/deploying, capture **fresh** server-only root0600
   booking/account preservation snapshots; export counts only. No ID/fingerprint
   exports. `artifacts/wb12_prepare_audits.py` attempted but failed before capture;
   it may generate a new snapshot name safely after access is restored.
5. Root-owned `/opt/biocad/tooling/scripts/check.py` must receive this task's checked
   runner (fixed `test/fallback` fixture setting) before server regression of new
   images. Refresh only owned tooling under deploy.lock, preserve unrelated paths
   and secrets. Keep real server fallback empty until live acceptance succeeds.
6. Check capacity. Prior WB-18 delivery hit4GiB MemAvailable guard on8GiB host;
   only private owned staging7 was temporarily stopped, preserving volumes and
   production/23 unrelated containers, then CI restored it. Do not lower guard,
   stop foreign/prod, prune globally or create resources. Any reuse of old helpers
   must update expected staging SHA to its actual current value.
7. Authorized workflow remains checked/reviewed feature→develop, full isolated
   server regression/staging smoke, checked promotion→main, exact-digest production
   smoke, then release aliases/Allure. No task/release completion until gates pass.

Useful ignored helpers: `github_ops.py` (gh/git without token argv), `server_ops.py`,
`run_logged.py`, `wb06_check_staged_secrets.py`, `wb06_check_doc_links.py`.
Old `wb18_delivery.py` is documentation-only/old PR42/43: never run unmodified.
