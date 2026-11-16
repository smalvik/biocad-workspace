# WB-11 booking deadlock — actual evidence

Issue [#34](https://github.com/smalvik/biocad-workspace/issues/34), discovered during
[WB-08 #33](https://github.com/smalvik/biocad-workspace/issues/33).
Branch `fix/wb-11-booking-deadlock`, base develop 82d14a4 plus carried WB-07
post-release notes a2657f90a1d3f4741933073b9485414d6ed3e76e.

Initial real disposable run `biocad-wb08-probe-4ae91ea542c7`:
seven guard cases passed, the outer race-sensitivity check failed. Red intentionally
removed exclusion in a new child DB; green restored the exact constraint and used
two real Uvicorn processes running unchanged Booking routers. Both INSERTs reached
the PostgreSQL advisory gate; after release, GiST exclusion checking produced an
actual transaction deadlock. HTTP process log contains `asyncpg.exceptions.DeadlockDetectedError`,
SQLSTATE `40P01`, waiting on two transaction ShareLocks. One HTTP response was 500.
The probe then hit a missing `X-Request-ID` while recording the unexpected response;
that secondary assertion is not the root failure. Non-overlap was never violated
with the constraint present. The owned child DB and disposable Compose project were removed.

[Initial launcher log](../../artifacts/WB-08-focused-initial.log),
[actual Allure attachments including green.log and HTTP process exception](../../artifacts/WB-08-focused-4ae91ea542c7/allure-results).
Source base a2657f9 / dirty probe; no persistent environment fault injection.

After bounded full-transaction `40P01` retry, the same probe passed in
`biocad-wb08-probe-cb962a619f85`, test container bounded to 768 MiB / one CPU:
**8 outer checks passed**, including seven environment/ownership guards and one
real sensitivity gate. Nested actual red **exit 1, 2 failed** (two bookings/events
for the same interval); restored green **exit 0, 3 passed** (one 201/one 409 per
resource, one committed booking/event; adjacent/cancelled interval control passed).
The exact catalog definition was restored, both temporary HTTP processes stopped,
and the new owned database removed. Same base a2657f9 / dirty fix + draft WB-08 probe.

`python artifacts/wb08_focused.py` through `artifacts/run_logged.py`:
[successful actual log](../../artifacts/WB-11-deadlock-original-probe.log),
[proof/Allure](../../artifacts/WB-08-focused-cb962a619f85/allure-results).
WB-08 probe remains outside the WB-11 commit; the fix has its own three real
PostgreSQL-error HTTP regressions. Those deterministic injections test retry handling;
they are explicitly distinct from the real deadlock cycle captured above.

Final standalone WB-11 full **20261115T232844Z-108797 passed 240 checks**:
103 Booking/delivery, 24 Assistant, 20 Worker, 2 persistence, 5 recovery phases,
26 Vitest and 60 Playwright; **35 commands exit 0**, **214 raw Allure results**.
Base a2657f9 / dirty fix-only tree, no WB-08 draft probe in this full run.
[Run metadata](../../artifacts/20261115T232844Z-108797/run.json),
[actual full log](../../artifacts/WB-11-deadlock-regression-native.log).
Committed head **2bc728e58d306997e4af4535f043857e540653f8** passed
[PR #35 CI 43775620397](https://github.com/smalvik/biocad-workspace/actions/runs/43775620397),
with explicit agent self-review (not independent human approval), merged develop
**75f661fcd75670bf3fce9efa7e3fe37c5bc9ef64** on 15 November 23:42:54 UTC
/ 16 November 02:42:54 Moscow. Post-merge server/staging workflow
[43776298717 PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43776298717):
real server **20261115T234957Z-36f94f**, clean75f661f, **240 checks / 35 commands exit 0**,
**215 raw Allure** including staging smoke. Completed WB-08 PR #36, promotion #37 →
main **5364c9e05505041e0035ea1b28adef99c6f61346**; [main 43779639648](https://github.com/smalvik/biocad-workspace/actions/runs/43779639648) **PASS**,
combined **248 checks / 224 raw server Allure**. Published patch **v1.4.1**, both
persistent environments updated. [Final release/public/preservation evidence](WB-08-remote.md).
First standalone full attempt **20261115T232051Z-64f160** stopped at **102 passed /
1 failed**: retry/exhaustion worked, but a subsequent manual-retry test interval
randomly overlapped another parameter case and correctly returned 409. The fixture
now gives those cases separate days. [Original log retained](../../artifacts/WB-11-deadlock-regression.log).
Second full attempt **20261115T232342Z-2e1288** again had **102 passed / 1 failed**:
the original blocking 20-request test hit a ReadTimeout. Real PostgreSQL logs show
a cascade of ordinary-INSERT GiST transaction deadlocks; bounded retry alone was
insufficient under heavy same-slot contention. [Actual second log](../../artifacts/WB-11-deadlock-regression-final.log).
The final change uses native PostgreSQL `INSERT ... ON CONFLICT DO NOTHING RETURNING`
against all usable existing constraints, then checks the same idempotency key to
return replay or conflict. No named exclusion dependency is introduced into SQL;
the WB-08 missing-constraint sensitivity experiment remains possible in its private DB.
Three-attempt `40P01` retry stays as a fallback, not the normal contention mechanism.
The actual promotion included this fix and completed WB-08 together after separate checked
develop PRs, following the existing feature-plus-conditional-fix delivery process.
No LLM calls, paid resources, Booking migration or persistent data mutation.

PostgreSQL describes transaction-level/session advisory locks and deadlock victim
rollback in [the official locking documentation](https://www.postgresql.org/docs/current/explicit-locking.html).
Native exclusion/unique conflict arbitration and `RETURNING` semantics:
[PostgreSQL INSERT](https://www.postgresql.org/docs/17/sql-insert.html).
