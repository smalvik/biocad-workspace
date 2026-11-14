# Development process, testing, releases and deployment

1. Issue must have story, acceptance criteria, priority, dependencies, design refs and test plan. One issue = one branch = one PR unless explicitly approved otherwise.
2. Start from latest `develop`, create `feat/wb-XX-topic`, `fix/wb-XX-topic`, `chore/...`, `test/...`, `ci/...` or `docs/...` by project convention. Conventional Commits standardizes **commit messages**, not branch names. Examples: `feat(booking): enforce idempotency`, `test(booking): cover concurrent requests`, `docs: document C2 architecture`.
3. In branch, update unit/integration tests; E2E Playwright for user-visible frontend changes; for backend/infrastructure include applicable integration and service smoke. Always test real PostgreSQL concurrency and relevant RabbitMQ/Mailpit plumbing. Use Allure labeling `run_type=smoke|regression`, `environment=local|staging|prod`, SHA, release version where known.
4. Run tests, static checks, type checking and review. Attach **real** test results, failures and limitations to PR. Produce `docs/changes/WB-XX.md` *after task is completed* (change note, not invented release).
5. Merge into `develop` only after checks/review; run **whole regression** rather than just changed tests. Deploy same candidate immutable digest to staging with deterministic mock seed, run regression/UI walkthrough.
6. After verified staging, issue `1.MINOR.PATCH` SemVer release; major fixed 1 for assignment. Increase minor for feature release and patch for bugfix release; source tag/release notes track one or more tasks. Do not version every merged branch automatically.
7. Build images once, upload to Docker Hub with version tag and immutable SHA/digest; promote same digest. Publish/update `latest` only **after passing validation** and keeping digest release record. A server hook must **pull and start** prebuilt images, not ambiguously rebuild code in prod; avoid trusting unsigned payloads. Ubuntu 22.04 Docker + Compose, health gates and rollback to previous digest.
8. `/releases` UI fetches published release metadata, not demo mock history; include date, improvements/fixes, links to real PR, digest, checks. When none published: genuine empty state.
9. Secrets through environment injection and CI encrypted secrets, minimum token scopes. Manual approval required for pushing remote branches, creating infrastructure, releasing or production deployment; never echo token/credentials.
10. `AI-LOG.md` records authored and agent contributions honestly; the README states time spent, decisions, limitations, C1/C2 and ADRs. Demo includes intentional broken race test against **isolated** DB only, then restore constraint; ship only passing version.

## Per-task change note template
```md
# WB-XX · Summary
- Status: completed / tested / merged / released (distinguish!)
- User visible effect:
- Implementation / architecture:
- Tests actually run + outcome:
- PR / commit SHA / Allure links:
- Risks / follow-ups:
```

## Full timeline target
Day 1: WB-01 core infra, WB-02 DB correctness + baseline map; Day 2: WB-03/04/05 UI, WB-06 real AI/MCP, WB-07 email; Day 3: hardening WB-08/09/10/17/18, optional P1, staging→real publish. Do not cut P0 for bonus features.
