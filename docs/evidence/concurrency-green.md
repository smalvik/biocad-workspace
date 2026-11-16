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
Published **v1.4.1**, clean main **5364c9e05505041e0035ea1b28adef99c6f61346**;
[main CI/server](https://github.com/smalvik/biocad-workspace/actions/runs/43779639648) PASS. Real server **20261116T002540Z-52c71a**
again records genuine RED exit 1 / 2 failed and GREEN exit 0 / 3 passed,
same oracle hash above, exact catalog restoration and owned database removed.
[Actual main GREEN output](../../artifacts/WB-08-main-delivery/server/5364c9e05505041e0035ea1b28adef99c6f61346/20261116T002540Z-52c71a/green-pytest.log),
[main structured proof](../../artifacts/WB-08-main-delivery/server/5364c9e05505041e0035ea1b28adef99c6f61346/20261116T002540Z-52c71a/race-proof.json),
[final delivery evidence](WB-08-remote.md).
Open [Allure v1.4.1](https://biocad.smalvik.dev/allure/v1.4.1/):
**Behaviors → race-red-green → Race sensitivity: genuine red FAIL, restored green
PASS (disposable DB only)**, then **green.log**. Both attachments actually opened
in public desktop/mobile browser checks with **zero downloads**.
[Actual browser result](../../artifacts/WB-08-race-production-browser/run.json).
No runtime mutation flag; the published Booking image physically excludes probe/pytest.
