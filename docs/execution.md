# Aity Drive v1 - execution board

Living status of the multi-day, multi-agent build-out. SINGLE WRITER: the
orchestrator session updates this file; stream agents never push to meta.
The plan itself is `../specs/aity-drive-v1.md`; account steps are
`runbooks/publisher-accounts.md`; the Mac runner is `runbooks/mac-runner.md`.

Updated: 2026-08-25 (streams launched)

## Streams

| Stream | Repo | Status | Next action |
|---|---|---|---|
| S1 Android factory | `drive/android` | LAUNCHED 2026-08-25 | agent scaffolds overlay + CI, green main build with both Environment APK/AABs; report targetSdk vs API 36 |
| S2 Desktop factory | `drive/desktop` | LAUNCHED 2026-08-25 | agent scaffolds OEM overlay + CI, green AppImage on main; measure hosted-Windows build once |
| S3 Keycloak clients + DRIVE brand | `infra/keycloak`, `keycloak/themes` | LAUNCHED 2026-08-25 | tofu clients both envs (apply authorized by Raul 2026-08-25), DRIVE brand + e2e at both viewports |
| S4 Renovate + CI docs | `drive/meta` | LAUNCHED 2026-08-25 | renovate config + weekly schedule + docs/ci.md; verify token inheritance |
| S5 iOS factory (authoring) | `drive/ios` | LAUNCHED 2026-08-25 | scaffold overlay/fastlane/CI, everything `macos`-tagged and manual; UNVERIFIED until the Mac runner exists |
| S6 Discovery surfaces | `aity-platform` (branch `drive-apps-card`) | LAUNCHED 2026-08-25 | Magistrate card + email footers + phone-viewport e2e; branch only, NO main push |
| Later | `drive-theme`, aity.ro | HELD | store links go in only when real listing URLs exist (theme repo goes live on pod restart) |

## Done

- [x] 18 decisions grilled; CONTEXT.md, ADRs 0001-0005, spec, maintenance loop (2026-08-25)
- [x] Subgroup `aity-cloud/drive`: meta, certificates, android, ios, desktop
- [x] GitHub mirrors wired (deploy keys + `GITHUB_MIRROR_KEY` + `ci/mirror.yml`), verified on meta
- [x] `aity-tech/drive-desktop` archived; workspace AGENTS.md lists `drive/`
- [x] Runbooks: publisher accounts, Mac runner

## Needs Raul (the only human steps)

- [ ] D-U-N-S request (start FIRST - gates Apple, Google, Azure; runbook step 1)
- [ ] Apple Developer Program org enrolment + DSA trader + EU invoicing (runbook step 2)
- [ ] Google Play organisation account + verification (runbook step 3)
- [ ] Azure Artifact Signing identity validation (runbook step 4)
- [ ] Register the personal Mac as the `macos` group runner (mac-runner runbook) - unblocks S5 verification and S1/S2 smoke jobs
- [ ] Buy GitLab compute minutes for the hosted Windows job
- [ ] VPN up when S3 reaches `tofu apply` (if it reports the gate)
- [ ] Merge decision on S6's `drive-apps-card` branch (platform commit-type lockdown is Raul's call)

## Stream reports

(appended by the orchestrator as agents complete)
