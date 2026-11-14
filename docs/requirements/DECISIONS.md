# Approved decisions

## 2026-11-14 — WB-02 promotion into main before release

User instruction: «запуш ветку, смержи в develop и main, от develop создай WB-03».
This explicitly approves pushing WB-02 and merging its checked result into
develop and then main via PRs, retaining the task branch. CI must pass before
each merge; the complete available regression runs after integration.

This is an approved exception to the release-only main policy for the current
WB-02 snapshot. It does not authorize a GitHub Release, registry publishing,
cloud resource creation or deployment. WB-03 starts from integrated develop.
