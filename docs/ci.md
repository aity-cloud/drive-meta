# drive CI - what runs where

The subgroup's shared pipeline surface. The standing loop around it
(response targets, the Bump ritual, Renovate MR handling) is
`docs/maintenance.md`; versioning and the per-Factory pipeline stages are
decisions 8 and 13 of `specs/aity-drive-v1.md`. Vocabulary: `CONTEXT.md`.

## meta (this repo)

meta has no build; its pipeline is two jobs:

- **mirror:github** (`ci/mirror.yml`, included by every mirrored repo of
  the subgroup): pushes `main` + all tags to the public GitHub twin
  `github.com/aity-cloud/drive-<name>` over SSH with the per-repo write
  deploy key `GITHUB_MIRROR_KEY`. Runs on main pushes and on tags; MR
  pipelines never mirror; if the key variable is absent the job does not
  exist at all. CI is the ONLY writer of a Public Mirror (ADR 0004).
- **renovate**: RETIRED HERE 2026-09-02. One estate-wide Renovate now
  sweeps the whole `aity-cloud` group DAILY from
  `aity-cloud/infra/estate-updates`; this subgroup's rules moved there as
  repo-scoped `packageRules`, including the ADR 0001 restriction that a
  Factory only ever moves CI job images, fastlane Gemfiles and annotated
  Pins. Nothing about what Renovate proposes here changed - only where it
  runs from, and how often.

What Renovate proposes across the subgroup: CI job image bumps
(gitlabci), fastlane bumps through the android/ios Factories' Gemfiles
(bundler), and the annotated Pins:

```yaml
variables:
  # renovate: datasource=github-tags depName=owncloud/android
  UPSTREAM_TAG: "v4.8.3"
```

An MR on an `UPSTREAM_TAG` is a SIGNAL that upstream released, not a
mergeable change - the Bump is the human ritual in `docs/maintenance.md`.
Nothing auto-merges; every Renovate MR waits for a human disposition.

## Factories and certificates

Each Factory documents its own pipeline (materialize -> build -> smoke ->
publish-staging -> promote -> mirror) in its own repo; the shared pieces
are the included `ci/mirror.yml` and the Renovate sweep above. The
private `certificates` repo has no pipeline and no mirror - it is the
fastlane match store and never leaves GitLab.

## Variables

| Variable | Where | Status (2026-08-25) | Purpose |
|----------|-------|---------------------|---------|
| `GITHUB_MIRROR_KEY` (file) | each mirrored repo (meta, android, ios, desktop), protected | set on all four (minted by `scripts/mint-mirror-keys.sh`); absent on `certificates` by design | mirror push deploy key, one per repo, rotation = re-run the script |
| `GITLAB_TOKEN` | `aity-cloud` group, protected + masked | inherited and verified visible to this project (neither the drive subgroup nor meta overrides it); protected, so it reaches protected refs only - `main` here is protected, and the weekly schedule runs on `main` | default for `RENOVATE_TOKEN`: gitlab.com Free cannot mint group access tokens, so the group's semantic-release token (api + write_repository) doubles as the Renovate bot token |
| `RENOVATE_TOKEN` | drive subgroup (optional override) | not set | takes precedence over the `GITLAB_TOKEN` default if a dedicated bot token ever exists |
| `GITHUB_COM_TOKEN` | drive subgroup (optional) | not set | raises github-tags rate limits for the three upstream watches; unauthenticated is fine at this repo count |
| signing + store secrets (`ASC_*`, `MATCH_*`, `ANDROID_UPLOAD_*`, `PLAY_SERVICE_ACCOUNT_JSON`, `AZURE_*`) | factory projects only, protected + masked, tag-protected refs | arrive with the M0 publisher accounts | authoritative map: `docs/runbooks/publisher-accounts.md` section 5; never on meta, never on a Public Mirror |

## Schedules

- Weekly Renovate sweep on this repo: schedule 4405201, `15 6 * * 1`
  Europe/Bucharest (Mon 06:15, staggered after crate's Mon 06:00 sweep),
  variable `RENOVATE=true`, ref `main`, active.
