# WB-09 follow-up #27 — Allure browser viewing

User request: open interactive reports directly in the browser, rather than download GitHub HTML assets.
This infrastructure change retains published release artifacts as the source of report content.
No inference requests, schema changes, new cloud resources or changes to shared ingress are needed.

## Source and local proof

- Issue [#27](https://github.com/smalvik/biocad-workspace/issues/27), branch `ci/wb-09-allure-web`
  from develop 887bcc1; carried completed WB-06 notes as 12151eb.
- Code 4e295a1 plus reviewed relative-redirect fix
  **403c64356fddf54c2f27d05b47299160f5be5c75**.
- Local full `python scripts/check.py --run-type regression`,
  **20261115T173054Z-928df1**, base12151eb / tree dirty: **209 checks passed**
  (97 Booking/delivery +24 Assistant +2 persistence +26 Vitest +60 Playwright),
  all 20 commands exit 0, **183 raw Allure results**.
  [Log](../../artifacts/WB-09-allure-regression.log).
- Real published v1.3.0 report assets downloaded and SHA256/size verified using
  `publish_allure.py`. Actual Nginx Web container + HTTP/source/checksum smoke passed;
  four desktop/mobile regression/live report navigation checks passed, no download events.
  After tightening relative redirects, rebuilt Nginx and repeated all four cases plus
  HTTP smoke successfully. [Final local metadata](../../artifacts/WB-09-allure-local-browser-final/run.json),
  [log](../../artifacts/WB-09-allure-local-browser-final.log).
- Clean head [CI 43742757454](https://github.com/smalvik/biocad-workspace/actions/runs/43742757454)
  passed 209 checks and immutable publication. Earlier43742287244 was cancelled after
  synchronization of the relative-redirect fix; it is not counted as final-head success.
- [PR #28](https://github.com/smalvik/biocad-workspace/pull/28) reviewed explicitly as
  agent self-review and merged develop **fd81f82cb0d064f766d4a70e6adc5ca29eca5616**.
  Independent human approval is not claimed.

## Publication contract

Nginx `/allure` redirects relatively, retaining HTTPS behind Traefik. `/allure/`
serves inline HTML from a separate read-only `/opt/biocad/public/allure` mount;
missing reports return404, directory listings disabled, no SPA fallback.
Only curated standalone HTML and public manifest/hash metadata enter that directory;
private raw report trees, backups and credentials are not mounted.

Restricted `publish-allure` accepts only a complete manifest equal to current production.
It uses the fixed public GitHub repository, published stable release, exact asset URLs,
SHA256 digests, size bounds and complete released/deployed manifest equality. Downloads
and staging remain outside the public mount. Publication preserves immutable version HTML
and replaces latest atomically; separately verified live evidence can be appended once.
Main CI publishes after release and verifies public inline/type/source/checksum.

The root-owned bootstrap completed, the existing v1.3.0 regression/live assets were
successfully verified and staged through the restricted CI key, and a real arbitrary
SSH shell attempt was still rejected. The earlier bootstrap attempt did not execute
because automatic approval review was temporarily unavailable due to a usage limit;
the same action succeeded through approval review after reset, with no bypass.

## Remote validation

[Develop43744036350](https://github.com/smalvik/biocad-workspace/actions/runs/43744036350)
completed success: full checks/publication, clean server regression
**20261115T180349Z-c77610**,209 checks,20 commands exit 0, **184 raw Allure results**
(183 regression + staging smoke). Staging source fd81f82 /1.3.1.
[Downloaded evidence](../../artifacts/WB-09-allure-develop-server/).
Independent actual staging inline/type/source/checksum smoke passed for all three report paths;
[safe metadata](../../artifacts/WB-09-allure-staging-inline-smoke.json).
[Main promotion PR #29](https://github.com/smalvik/biocad-workspace/pull/29)
passed [checks/publication43744095688](https://github.com/smalvik/biocad-workspace/actions/runs/43744095688).
PR #29 was reviewed as agent self-review after green staging and merged main
**8d8cf08f9f43c3568c6bd737053101bf8c80ac7d**.
[Main 43745466108](https://github.com/smalvik/biocad-workspace/actions/runs/43745466108)
completed **success**, including main-source server regression, staging, exact
production image promotion, HTTPS smoke, version/latest verification, published release,
restricted Allure publication and public inline/type/source/checksum smoke.

Published **[v1.3.1](https://github.com/smalvik/biocad-workspace/releases/tag/v1.3.1)**
at **2026-11-15 18:26:47 UTC / 21:26:47 MSK**. Clean main server run
**20261115T181849Z-fd2bb5** passed 209 regression checks, all 20 commands exit 0;
**185 raw Allure results** =183 regression +stage/prod smoke (26 Vitest separately).
The public-publication HTTP smoke is an additional result in the workflow artifacts.
[Downloaded main evidence](../../artifacts/WB-09-allure-main-delivery/).

## Verified public URLs and browser acceptance

- [Latest regression](https://biocad.smalvik.dev/allure/).
- [v1.3.1 regression](https://biocad.smalvik.dev/allure/v1.3.1/).
- [v1.3.0 regression archive](https://biocad.smalvik.dev/allure/v1.3.0/).
- [v1.3.0 actual free-model acceptance](https://biocad.smalvik.dev/allure/v1.3.0/live/).

Independent public HTTPS acceptance with the exact main E2E digest:
HTTP inline/type/full-manifest/body-checksum smoke passed, plus **4 desktop/mobile
interactive report navigation cases passed, launcher exit 0, zero download events**.
Relative latest/archive redirects also checked. [Metadata](../../artifacts/WB-09-allure-production-browser/run.json),
[log](../../artifacts/WB-09-allure-production-browser.log),
[desktop screenshot](../../artifacts/WB-09-allure-production-browser/regression-desktop.png),
[mobile screenshot](../../artifacts/WB-09-allure-production-browser/live-mobile.png).
This task made **no new LLM inference requests**; the separately hosted real-provider
report retains its original v1.3.0 source/cost evidence.

Both environment manifests equal the full main candidate; all 12 BIOCAD containers healthy.
Production previous v1.3.0 retained; backup **20261115T182546-e80410.dump**,29,856 bytes.
[State metadata](../../artifacts/WB-09-allure-server-state.json).
Each environment retains 7 bookings/12 accounts; all original row fingerprints unchanged,
comparison performed only on-server, exporting only aggregate counts.
[Aggregate proof](../../artifacts/WB-09-allure-data-after.json).
All 23 unrelated containers preserve IDs/images/start times/restart counts and sampled
HTTP statuses. Baseline already contained URLError/401/404, so unrelated URL health is
not claimed. [Preservation proof](../../artifacts/WB-09-allure-preservation-proof.json).

Actual commands: `git switch/cherry-pick/commit/push`; `gh issue/pr/run`;
`scripts/check.py`, Ruff, `scripts/publish_allure.py`, `scripts/check_public_allure.py`,
actual isolated Nginx and Playwright browser runner; root-owned bootstrap and restricted
publication/shell rejection through `artifacts/server_ops.py`; `remote_delivery.py stage/production/publish-allure`,
`check_public_allure.py`, `wb09_allure_production_browser.py`, preservation checks.
Baselines contain only safe
container metadata; booking/account snapshots remain on-server, exporting only aggregate counts.
