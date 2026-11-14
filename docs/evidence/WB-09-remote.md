# WB-09 actual delivery — v1.0.0

Published [v1.0.0](https://github.com/smalvik/biocad-workspace/releases/tag/v1.0.0).
Production: https://biocad.smalvik.dev (fictional accounts e01–e12 / demo-workspace).
Main source: `e7ba97b00f0e1a5f246326f732062b06c8f1a301`.

- [Main workflow 43626386129](https://github.com/smalvik/biocad-workspace/actions/runs/43626386129): all jobs PASS.
- **92 passed = 56 Booking/delivery + 2 Assistant + 2 persistence + 10 Vitest + 22 Playwright**.
- Complete server regression used prebuilt digests, real PostgreSQL/RabbitMQ/Mailpit and isolated test storage; no image builds on the host.
- Persistent staging smoke and production HTTPS/login/me/floors/logout/source smoke PASS.
- Server Allure: **84 passed** = 82 regression results + staging/prod smoke; Vitest 10 separately.
- [Standalone Allure HTML](https://github.com/smalvik/biocad-workspace/releases/download/v1.0.0/index.html), download/open locally.
- [Exact published image manifest](https://github.com/smalvik/biocad-workspace/releases/download/v1.0.0/candidate.json).
- Version/latest aliases verified against staging-tested digests for the three existing runtime services.
- Independent public HTTPS desktop/mobile smoke: **2 passed**, source main SHA above,
  [metadata](../../artifacts/WB-09-production-browser-final/run.json), [log](../../artifacts/WB-09-production-browser-final.log), actual screenshots/Allure saved alongside.
- First ad hoc browser invocation had 2 passing tests but PowerShell interpreted Docker pull stderr
  as NativeCommandError. Launcher streams were merged; independent repeat exited **0**, 2 passed.
- [Preservation proof](../../artifacts/WB-09-server-preservation-proof.json): all **23** preexisting
  containers retained IDs, image references and start/restart timestamps. Sample HTTP statuses
  match their predeployment baseline; this does not claim all sample URLs were healthy before.

WB-09 [PR #11](https://github.com/smalvik/biocad-workspace/pull/11) -> develop `f3a6e8f`.
Conditional fix [PR #14](https://github.com/smalvik/biocad-workspace/pull/14) -> `f5336c8`.
[Promotion #12](https://github.com/smalvik/biocad-workspace/pull/12) -> main SHA above.
Reviews explicitly identified themselves as agent self-reviews, not independent human approval.

Serialization proof: push `43625348918` and promotion PR `43625353266` for identical
`f5336c88e9e7db947607063476b45711f3165d98`. PR package 18:15:50–18:18:00 UTC;
push package 18:18:02–18:18:25 UTC, reusing identical seven-image digests.
[Actual proof](../../artifacts/WB-11-serialization-proof.json).

This release is an incremental authenticated map + Booking API baseline. Employee lookup,
form, real MCP/LLM and notifications are not claimed as shipped by v1.0.0.
