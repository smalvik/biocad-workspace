# WB-08 / WB-11 delivery evidence — 16 November 2026 Moscow

WB-08 issue [#33](https://github.com/smalvik/biocad-workspace/issues/33) and actual
deadlock defect [#34](https://github.com/smalvik/biocad-workspace/issues/34) remain
separate purpose-specific branches/PRs. Reviews are explicit agent self-review;
independent human approval is not claimed.

| Gate | Actual result |
|---|---|
| WB-11 fix [PR #35](https://github.com/smalvik/biocad-workspace/pull/35), head 2bc728e | [CI 43775620397 PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43775620397); merged develop **75f661fcd75670bf3fce9efa7e3fe37c5bc9ef64**, 15 November 23:42:54 UTC / 16 November 02:42:54 Moscow |
| WB-11 post-merge | [43776298717 PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43776298717); full CI/server regression and persistent staging smoke |
| WB-08 [PR #36](https://github.com/smalvik/biocad-workspace/pull/36), head c511f34 | [CI 43777055529 PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43777055529); merged develop **05e08e620aae6089a748400593d9cf0fdad0c9d4**, 16 November 00:00:38 UTC / 03:00:38 Moscow |
| WB-08 post-merge | [43777851963 PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43777851963); full CI/server regression and persistent staging smoke |
| Promotion [PR #37](https://github.com/smalvik/biocad-workspace/pull/37) | [CI 43777960805 PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43777960805); merged main **5364c9e05505041e0035ea1b28adef99c6f61346**, 16 November 00:18:57 UTC / 03:18:57 Moscow |
| Main | [43779639648 PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43779639648); complete CI/server regression, staging/production smoke, exact digest promotion, version/latest aliases, published release and public Allure |

WB-11 native-path local **20261115T232844Z-108797** passed **240 checks**, all
**35 commands exit 0**, **214 raw Allure**; its real server **20261115T234957Z-36f94f**
at clean source75f661f passed the same **240**, **35 commands exit 0**,
**215 raw Allure** including staging smoke. [Actual server artifacts](../../artifacts/WB-11-deadlock-develop-delivery).
The initially observed true 40P01/500, fixture overlap and retry-only deadlock cascade
are preserved in [the separate defect evidence](WB-11-booking-deadlock.md).

WB-08 local **20261115T233744Z-14784d** passed **248 outer checks** / **222 raw Allure**,
source2bc728e/tree dirty. Clean feature CI **20261115T235137Z-69c380** at c511f34
passed the same **248 / 222**, all **35 commands exit 0**. Real server develop run
**20261116T000713Z-116055**, clean source05e08e6, passed **248 outer checks**, all
**35 commands exit 0**, **223 raw Allure** including staging smoke.
111 Booking/delivery +24 Assistant +20 Worker +2 persistence +5 outage/recovery phases
+26 Vitest +60 desktop/mobile Playwright. Vitest is separate from Allure.

Actual child commands repeatedly produced **red exit1 / 2 failed** with the missing
child constraint, then **green exit0 / 3 passed** after exact catalog restoration.
For both desk/meeting room, two INSERTs were observed blocked at the database gate;
red had two 201 / two committed bookings/events; green had one 201 + one 409 /
one booking/event. Same oracle SHA256
`55547fa530e21ff54606dd626cb004bf38e1e2d3848cefb0f98cf851acfbcc23` across local,
clean CI and real server. Raw child failures/results are preserved in the passing
outer Allure sensitivity case, not counted again in the 248 headline or disguised as xfail.
The private creation-owned DB is removed; probe and pytest are absent from the runtime.
[RED](concurrency-red.md), [GREEN](concurrency-green.md),
[clean CI proof](../../artifacts/WB-08-pr-checks/20261115T235137Z-69c380/race-proof.json),
[real server proof](../../artifacts/WB-08-develop-delivery/server/05e08e620aae6089a748400593d9cf0fdad0c9d4/20261116T000713Z-116055/race-proof.json),
[local runtime-boundary inspection](../../artifacts/WB-08-runtime-boundary-local.json).

Same-SHA develop push and promotion PR manifests match in **all nine digests/fields**,
strict schema2, candidate version1.4.1. [Actual build-once proof](../../artifacts/WB-08-build-once-proof.json).
Main builds its new source SHA once; staging and production use that exact nine-image manifest.
[Published v1.4.1](https://github.com/smalvik/biocad-workspace/releases/tag/v1.4.1),
16 November **00:35:01 UTC / 03:35:01 Moscow**, non-draft/non-prerelease, target main5364c9e.
[Exact published manifest](https://github.com/smalvik/biocad-workspace/releases/download/v1.4.1/candidate.json).
No migration, Booking authority weakening, frontend-flow change or new LLM calls.
All LLM regression remains explicitly scripted, with real MCP/RabbitMQ/PostgreSQL/Mailpit.

Fresh original booking/account checksums remain **only on the server**, root-only;
no individual identifiers/fingerprints were exported. After WB-11/WB-08 staging,
each environment retains **7 original bookings / 12 original accounts**, changed/missing0.
[Aggregate-only staging check](../../artifacts/WB-08-data-after-staging.json).

## Final main delivery and public browser evidence

Clean main CI **20261116T001913Z-9b9f5e** and real server
**20261116T002540Z-52c71a**, source **5364c9e05505041e0035ea1b28adef99c6f61346**, each passed
**248 outer checks / 35 commands exit 0**. Server contains **224 raw Allure results**:
222 regression + staging/production smoke; 26 Vitest checks are separate. Allure may
fold repeated phase/history identities in its UI; raw-file counts are not a visible
case-count claim. Expected child RED failures are attachments, not failed release checks.
[Main CI metadata](../../artifacts/WB-08-main-checks/20261116T001913Z-9b9f5e/run.json),
[actual server metadata](../../artifacts/WB-08-main-delivery/server/5364c9e05505041e0035ea1b28adef99c6f61346/20261116T002540Z-52c71a/run.json),
[main race proof](../../artifacts/WB-08-main-delivery/server/5364c9e05505041e0035ea1b28adef99c6f61346/20261116T002540Z-52c71a/race-proof.json),
[actual red output](../../artifacts/WB-08-main-delivery/server/5364c9e05505041e0035ea1b28adef99c6f61346/20261116T002540Z-52c71a/red-pytest.log),
[actual green output](../../artifacts/WB-08-main-delivery/server/5364c9e05505041e0035ea1b28adef99c6f61346/20261116T002540Z-52c71a/green-pytest.log).
The unchanged oracle hash above, exact constraint restoration and owned-DB removal
were verified again at this clean published source.

The actual published Booking runtime digest was inspected with networking disabled:
both mutation probe and pytest are physically absent.
[Published runtime inspection](../../artifacts/WB-08-runtime-boundary-published.json).
This is test-only fault injection, never a production constraint toggle.

- [Application](https://biocad.smalvik.dev): **4 public desktop/mobile checks PASS**,
  no booking writes or inference calls. [Actual result](../../artifacts/WB-08-production-browser/run.json).
- [Latest report](https://biocad.smalvik.dev/allure/) and
  [original free-model report](https://biocad.smalvik.dev/allure/v1.3.0/live/):
  **4 public desktop/mobile report checks PASS**, downloads=0.
  [Actual result](../../artifacts/WB-08-allure-production-browser/run.json).
- [Exact v1.4.1 report](https://biocad.smalvik.dev/allure/v1.4.1/): **2 additional
  desktop/mobile race-evidence checks PASS**, downloads=0. Both actually expanded
  **red.log** (`NONOVERLAP_INVARIANT`, `2 failed`) and **green.log** (`3 passed`).
  In Allure open **Behaviors → race-red-green → Race sensitivity: genuine red FAIL,
  restored green PASS (disposable DB only)**, then those attachments.
  [Actual result](../../artifacts/WB-08-race-production-browser/run.json),
  [desktop screenshot](../../artifacts/WB-08-race-production-browser/race-evidence-desktop.png),
  [mobile screenshot](../../artifacts/WB-08-race-production-browser/race-evidence-mobile.png).

HTTP inline/content-type/source/checksum publication smoke also passed. Original
v1.3.0 live results remain historical acceptance, not new provider calls.

## Preservation and rollback record

Both persistent environments now run **v1.4.1 / 5364c9e05505041e0035ea1b28adef99c6f61346**,
all **14 own containers running/healthy**. Original **7 bookings / 12 accounts per
environment** remain byte-equivalent in the server-only comparison, changed/missing=0.
[Final aggregate-only data check](../../artifacts/WB-08-data-final.json).
All **23 unrelated containers** retain their IDs/images/start times/restart counts.
The sampled HTTP responses match baseline; their pre-existing URLError/401/404 do not
prove those applications healthy. [Actual comparison](../../artifacts/WB-08-preservation-proof.json).
No proxy restart, DNS change, daemon reconfiguration or foreign-project mutation.

Notification Worker is healthy in both environments, **7 sent / 7 actually captured
Mailpit messages** each, pending outbox/jobs=0 and delivery/invalid queues ready/unack=0.
[Actual notification audit](../../artifacts/WB-08-final-notifications.json),
[filtered server state](../../artifacts/WB-08-final-server-state.json).
Production previous manifest **v1.4.0 / 5decd64** is retained. Validated pre-deploy
backups: staging **20261116T003317-82d4f7.dump / 29,424 bytes**, production
**20261116T003346-f86bc8.dump / 30,190 bytes**. Dumps/individual fingerprints remain
root-only on the server and are not release assets.

No Booking migration or frontend flow change; no new LLM call, paid inference,
external SMTP delivery or persistent production fault injection. The whole PRD is
not complete. Next unfinished P0: **WB-10 delivery documentation** (WB-09 already shipped).
Post-release documentation checks: `python scripts/check_policy.py` with WB-08 branch/title
context PASS; staged configured-secret scan PASS (15 files); relative Markdown links
147 checked, missing=0; `git diff --cached --check` PASS after removing a trailing blank line.
