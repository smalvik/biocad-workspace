# Concurrency RED — deliberately broken child schema, not for release

WB-08 issue [#33](https://github.com/smalvik/biocad-workspace/issues/33).
This is an actual mutation demonstration in a newly generated disposable database,
not a claim that the deployed schema permits overlap. Persistent staging/production
constraints are never touched. The missing-constraint configuration is **not for release**.

Actual command: `python artifacts/wb08_focused.py` (launcher
`python artifacts/run_logged.py artifacts/WB-08-focused-native.log python artifacts/wb08_focused.py`).
The same integration gate runs automatically inside `python scripts/check.py --run-type regression`.
Source base **2bc728e58d306997e4af4535f043857e540653f8**, working tree **dirty** with
the draft WB-08 probe. Parent source is the separately tracked WB-11 fix, PR #35.
Focused project **biocad-wb08-probe-9e3172dc0a8f**, 768 MiB/one CPU test container,
real PostgreSQL, no host ports, fake credentials, two distinct HTTP processes.

The controller creates/migrates/seeds its own `wb08_<uuid>` database, proves matching
creation OID and ownership comment, removes only `bookings_no_overlap` there and verifies
its absence. For each D-15/M-03 case two authenticated fictional employees use different
keys. Both real INSERT transactions must be observed waiting at a PostgreSQL advisory
gate before release. The ordinary oracle always requires exactly one winner/event.

Actual nested command: `python -m pytest -q race_probe/invariant.py --alluredir=<temporary red>
-k two_process_confirmations`. It genuinely returns **exit 1: 2 failed, 1 deselected**.
Each failure is `NONOVERLAP_INVARIANT`, not a setup/import/auth error or an xfail.

| Case | Observed blocked INSERTs | HTTP | Committed confirmed | Outbox events |
|---|---|---|---|---|
| FreeDesk D-15 | 2 | 201, 201 | 2 | 2 |
| Meeting room M-03 | 2 | 201, 201 | 2 | 2 |

Exact oracle source SHA256 (identical in red and green):
`55547fa530e21ff54606dd626cb004bf38e1e2d3848cefb0f98cf851acfbcc23`.
[Actual red pytest output](../../artifacts/WB-08-focused-9e3172dc0a8f/red-pytest.log),
[actual structured proof and request IDs](../../artifacts/WB-08-focused-9e3172dc0a8f/race-proof.json),
[launcher log](../../artifacts/WB-08-focused-native.log).

The outer gate correctly recognizes that the invariant caught the deliberately missing
constraint; after restoring the schema it requires the genuine [GREEN](concurrency-green.md)
run before passing. Raw logs and structured raw Allure child results are attached to
the normal `Race sensitivity: genuine red FAIL, restored green PASS (disposable DB only)`
Allure case. The final whole local **20261115T233744Z-14784d** also passed **248 outer checks**,
all 35 commands exit 0, 222 raw Allure results; its independent child run again genuinely
failed both missing-constraint cases. [Actual full-run red output](../../artifacts/20261115T233744Z-14784d/red-pytest.log),
[full proof](../../artifacts/20261115T233744Z-14784d/race-proof.json).
Final clean CI/public report links will be recorded after actual delivery.
The earlier unexpected restored-green 40P01/500 remains a separate [WB-11 defect record](WB-11-booking-deadlock.md).
