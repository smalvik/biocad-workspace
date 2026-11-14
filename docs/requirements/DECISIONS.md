# Approved decisions

## 2026-11-14 — WB-02 promotion into main before release

User instruction: «запуш ветку, смержи в develop и main, от develop создай WB-03».
This explicitly approves pushing WB-02 and merging its checked result into
develop and then main via PRs, retaining the task branch. CI must pass before
each merge; the complete available regression runs after integration.

This is an approved exception to the release-only main policy for the current
WB-02 snapshot. It does not authorize a GitHub Release, registry publishing,
cloud resource creation or deployment. WB-03 starts from integrated develop.

## 2026-11-14 — Deliver CI/CD before the next product task

The user requested feature PR -> develop -> main -> automatic versioned Docker Hub delivery
and server update with fictional data, tests and Allure, preserving existing hosted apps.
This explicitly authorizes necessary branch/PR integration, image publication,
server configuration and deployment for WB-09. WB-03 was integrated separately first;
WB-09 stays on its own issue/branch. Continue WB-04 after delivery works.

User supplied DEPLOY_HOST/USER/PASS in local `.env`, explicitly instructed creating
an SSH key and storing its path, and renewed the Docker Hub PAT. Password is bootstrap-only;
admin key stays local, CI receives a separate restricted deploy key. Server inventory found
Ubuntu 24.04 and existing Traefik ingress. Adapt to it instead of replacing host
Nginx: production Web alone joins its existing ingress network; private project networks
keep API/data services isolated. Existing applications/proxy stay untouched.

PRs publish SHA candidates after checks; develop gets full regression and staging.
Main merge builds its own SHA candidate once, verifies it on staging, deploys exact digests
to production and performs HTTPS smoke. Version/latest aliases and GitHub release follow
successful production smoke. Baseline v1.0.0 is an honestly scoped incremental demo release,
not completion of all PRD tasks. No rebuild occurs between staging and production.
