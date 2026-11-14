# WB-09 delivery runbook

## Actual status

Implementation branch: `ci/wb-09-release-deploy`, [issue #10](https://github.com/smalvik/biocad-workspace/issues/10).
Runtime Compose, restricted SSH dispatcher and Actions jobs are implemented and tested locally.
**Working in production:** [v1.0.0](https://github.com/smalvik/biocad-workspace/releases/tag/v1.0.0),
https://biocad.smalvik.dev. Main workflow `43626386129` passed complete regression,
real server staging/prod smoke, digest promotion and release/Allure publication.
Registry/deployment gates are enabled after verified credentials/bootstrap.
[Actual evidence and preservation of 23 existing containers](../evidence/WB-09-remote.md).

## Delivery contract

| Event | Behavior after activation |
|---|---|
| Feature PR into develop | Policy + complete available checks + Allure. Same-repository PRs publish SHA candidates; forks never receive publishing credentials. No production update. |
| Merge into develop | Full regression; build/push immutable candidates; isolated complete regression on the server with fictional seed; update private staging and smoke. |
| develop PR into main | PR checks and candidates. Integration remains through a checked/reviewed PR. |
| Merge into main | Full regression; build one candidate set for the main SHA; server regression + staging smoke; promote those exact digests into production; HTTPS/session smoke. Only then add version/latest aliases and publish GitHub Release/evidence. |

Main's merge commit is a new source SHA. Its candidate is built once, then never rebuilt between staging and production.
Candidate repositories: `smalvik/biocad-web`, `biocad-booking`, `biocad-assistant`.
Test runners have separate `biocad-web-tests`, `biocad-booking-tests`, `biocad-assistant-tests`, `biocad-e2e` repositories.
All use `sha-<40-character-source-sha>` candidates. Only the three existing runtime services receive `v1.MINOR.PATCH` / `latest` aliases.
Notification Worker does not exist yet; no placeholder notifier image is published.

The first checked incremental delivery starts at `v1.0.0`. Subsequent published snapshots bump MINOR if their commits include `feat`, otherwise PATCH.
This does not version every PR. The GitHub Release is created only after production smoke, with exact digests, source, task-note links, `CHANGELOG.md`, `releases.json`, and a standalone Allure HTML asset.
Release publication is evidence of that incremental version, not a claim that all PRD capabilities are implemented.

`scripts/delivery_manifest.py` accepts only the complete seven-image set, allowed Docker Hub repositories, immutable SHA256 digests and strict source/version fields.
After pulling, both runtime and regression paths verify public OCI source/revision labels. Environment variables cannot disguise an older image as the new source revision.

## Bootstrap on the existing shared host

1. Obtain the exact administrator SSH key path and login from the owner. Use trusted existing `known_hosts` or verify its fingerprint through the server/provider before connecting. Do not reuse another project's key without confirmation.
2. Run `scripts/inspect_server.sh` read-only. Inventory existing Nginx/containerized proxies, domains, certificates, listening ports, Compose projects, Docker/Compose/Python versions, disk and RAM. Do not print `.env`, full container inspection or private keys.
3. Choose two unused loopback ports. `18080` production / `18081` staging were verified free during bootstrap. The bootstrap refuses collisions with existing projects/storage/network names and occupied ports.
4. Generate a new ed25519 CI deploy key in an ignored private directory. The administrator key remains local. Upload only the reviewed tooling bundle and CI **public** key to a new temporary directory on the server.
5. As administrator, run `python3 scripts/bootstrap_server.py --public-key /path/to/ci.pub --production-url https://biocad.smalvik.dev --staging-port 18081 --production-port 18080 --ingress-network naiditrenera_web` from that bundle. The last argument selects the verified existing Traefik network. Ubuntu 22.04 Python 3.10 is supported; the actual host is Ubuntu 24.04/Python 3.12. Existing Docker, Compose and sudo must be present; bootstrap does not upgrade the daemon.
6. Bootstrap writes only `/opt/biocad`, a dedicated `biocad-deploy` account/home, two BIOCAD entrypoints and its own sudoers file. Separate root-only random PostgreSQL/RabbitMQ/session secrets are generated per environment. Existing secrets/passwords are preserved on reruns. Its root-owned account home/public authorization cannot be replaced by the deploy account.
7. Actual ports 80/443 belong to existing Traefik, with Docker discovery, `le` ACME resolver and `naiditrenera_web` ingress. `compose.traefik.yaml` adds a uniquely named BIOCAD HTTPS route through labels only on production Web. The proxy hot-discovers it and obtains the certificate; no existing proxy restart/config replacement. Nginx remains inside the web image. `infra/nginx/biocad.conf.example` is an alternative template for a future **host Nginx** deployment, not installed on this host.
8. Store the restricted CI private key as `DEPLOY_SSH_KEY` and the verified host entry as `DEPLOY_KNOWN_HOSTS`. Test the forced command with `{"action":"status"}` on stdin. It rejects remote shell/scp commands, forwarding, PTYs, arbitrary paths, foreign image repositories and unsupported JSON operations. The user has no general Docker group membership.
9. Verify registry login and push rights using the renewed PAT; refresh `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN` GitHub Secrets. Use stdin / secret UI, never command-line token arguments or chat. Repositories must be public for the server's credential-free pulls. Confirm candidate anonymous pulls before enabling deployment.
10. Enable `REGISTRY_ENABLED=true` after credential verification, and `DEPLOY_ENABLED=true` after bootstrap, host trust, ingress/DNS inventory and restricted-key smoke. First production smoke waits for initial ACME certificate issuance. Run the feature PR/develop/main flow and attach actual remote evidence before marking WB-09 complete.

| Actions setting | Kind | Value/purpose |
|---|---|---|
| DOCKERHUB_USERNAME / DOCKERHUB_TOKEN | Secrets | Publisher identity and renewed Read & Write PAT |
| DOCKERHUB_NAMESPACE | Variable | `smalvik` |
| DEPLOY_HOST | Variable | Verified server address from local `.env` (DNS points to the same host) |
| DEPLOY_USER | Variable | `biocad-deploy`, created by bootstrap |
| DEPLOY_SSH_KEY / DEPLOY_KNOWN_HOSTS | Secrets | Dedicated restricted private key and verified host trust |
| PUBLIC_URL | Variable | `https://biocad.smalvik.dev` |
| REGISTRY_ENABLED / DEPLOY_ENABLED | Variables | Readiness gates, activated after verified bootstrap/credentials |

## Isolation and validation

`infra/compose.release.yaml` has no build instructions, source mounts or global container names. Its data networks/volumes are private per project.
Optional `compose.traefik.yaml` connects **only production Web** to the existing external ingress network; API/data services never join it.
`compose.host.yaml` publishes only Web on `127.0.0.1`. PostgreSQL, APIs, RabbitMQ and Mailpit stay internal.
Projects are `biocad-staging` and `biocad-production`; their data, credentials and ports differ.
Memory/CPU/log limits apply only to BIOCAD containers; the daemon and unrelated applications are not reconfigured.

Before server regression the dispatcher requires at least 6 GiB free disk and 4 GiB available RAM: the largest bounded regression phase can use roughly 3.4 GiB in addition to already running apps.
If inventory is smaller, stop and choose a reviewed resource plan; do not remove other apps/images or add swap silently.

Complete candidate regression uses `scripts/check.py --manifest ... --environment staging --run-type regression` with prebuilt runtime/test digests.
It creates disposable `biocad-check-<unique-id>` storage/network, exposes no ports, and never uses the persistent production DB for fault injection or direct SQL tests.
The regression transport is internal HTTP with `APP_ENV=local`; `REPORT_ENV=staging` labels the execution environment. This deliberate test configuration permits HTTP cookies without weakening persistent staging/production, which use Secure cookies.
Production additionally verifies real HTTPS login/me/floors/logout, Secure/HttpOnly/SameSite attributes, readiness and source SHA of all three services. Staging's loopback smoke checks login issuance/cookie flags and readiness.

Fictional seed is repeatable and preserves bookings/accounts/passwords. No real profiles or LLM credentials enter regression.
Allure result directories, browser screenshots and logs are fetched through the report-only dispatcher operation and uploaded as run-specific Actions artifacts (30 days for delivery).
Backup/secret files never enter the report bundle. A standalone Allure asset is attached only to a genuinely published release. Authenticated Playwright traces stay disabled.

## Failure and rollback

The dispatcher serializes all operations with a host file lock; Actions serializes server delivery jobs without cancelling them.
Before updating an existing DB it creates a root-only `pg_dump -Fc` and validates its catalog with `pg_restore --list`.
Pull failure leaves the running stack unchanged. Health/HTTP smoke failure restores the previous immutable image manifest; a failed first install stops only its own app containers and preserves its new data.
`current.json` changes only after success; `previous.json` records the prior successful image set.

For an explicit image rollback, send `{"action":"rollback","environment":"production"}` using `scripts/remote_delivery.py rollback` with the configured restricted-key secrets in the environment.
It backs up first, restores recorded images, and repeats smoke. A red staging run cannot authorize production; the attestation must exactly match every candidate digest and SHA.

**Database rollback is not automatic.** It could discard new bookings. Current migrations are additive; future changes need expand/contract compatibility. If schema restoration is required, preserve current data, verify the dump in a separate database, then agree on recovery/cutover explicitly.
No host-wide prune, `down` of another project, volume deletion, Nginx replacement or Docker restart is part of deployment.
Runtime logs are bounded. Monitor `/opt/biocad/reports`, backups and image storage; retention cleanup must stay scoped to BIOCAD and keep current/previous digests. Low-disk preflight stops new regression instead of pruning shared storage.

Implementation references: [workflow](../../.github/workflows/ci.yaml), [dispatcher](../../scripts/deploy_server.py), [manifest](../../scripts/delivery_manifest.py).
Primary documentation used: [Docker GitHub Actions](https://docs.docker.com/build/ci/github-actions/push-multi-registries/), [GitHub workflow triggers](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).
