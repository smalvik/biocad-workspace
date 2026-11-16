# Concurrency GREEN — restored real exclusion constraint

This is the restored phase of the same actual [RED experiment](concurrency-red.md),
source base **2bc728e58d306997e4af4535f043857e540653f8**, tree **dirty**,
project **biocad-wb08-probe-9e3172dc0a8f**. Separate WB-11 PR #35 supplies native
conflict arbitration plus bounded residual-deadlock handling; GiST remains the authority.

After red, only the new owned child database's probe rows/events are removed. The exact
original `pg_get_constraintdef` is reinstalled and compared equal before green starts.
The `[start,end)`/confirmed-only exclusion is never weakened in a shipped migration.

Actual command: `python -m pytest -q race_probe/invariant.py --alluredir=<temporary green>`.
Same single-winner oracle source SHA256 as RED:
`55547fa530e21ff54606dd626cb004bf38e1e2d3848cefb0f98cf851acfbcc23`.
Actual result **exit 0: 3 passed**:

| Case | Observed blocked INSERTs | HTTP | Committed confirmed | Outbox events |
|---|---|---|---|---|
| FreeDesk D-15 | 2 | 201, 409 BOOKING_CONFLICT | 1 | 1 |
| Meeting room M-03 | 2 | 201, 409 BOOKING_CONFLICT | 1 | 1 |
| Half-open/cancel control | — | Adjacent confirmations 201/201; own cancel 200; released interval 201 | HTTP control | Not separately counted |

Both temporary HTTP processes stop and the matching-creation database is removed;
`owned_database_removed=true` in the proof. The outer run has **8 passed** checks
(seven endpoint/credential/ownership guards and one real sensitivity gate); the child
fail/pass counts are kept separate, with original raw results/logs attached in Allure.

[Actual green output](../../artifacts/WB-08-focused-9e3172dc0a8f/green-pytest.log),
[actual proof/catalog comparison/request IDs](../../artifacts/WB-08-focused-9e3172dc0a8f/race-proof.json),
[outer actual run](../../artifacts/WB-08-focused-9e3172dc0a8f/run.json).
The ordinary blocking 20-request real HTTP test remains unchanged. Whole local
**20261115T233744Z-14784d** passed **248 outer checks**, all **35 commands exit 0**,
**222 raw Allure results**, source 2bc728e/tree dirty; nested green again **3 passed**.
[Actual full-run green output](../../artifacts/20261115T233744Z-14784d/green-pytest.log),
[full proof](../../artifacts/20261115T233744Z-14784d/race-proof.json),
[whole-run metadata](../../artifacts/20261115T233744Z-14784d/run.json).
Runtime image physically excludes both mutation probe and pytest;
[actual network-disabled inspection](../../artifacts/WB-08-runtime-boundary-local.json).
Clean CI/server/public report validation will be recorded when actually completed.
