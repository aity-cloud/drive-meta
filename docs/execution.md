# Aity Drive v1 - execution board

Living status of the multi-day, multi-agent build-out. SINGLE WRITER: the
orchestrator session updates this file; stream agents never push to meta.
The plan itself is `../specs/aity-drive-v1.md`; account steps are
`runbooks/publisher-accounts.md`; the Mac runner is `runbooks/mac-runner.md`.

Updated: 2026-08-25 13:0x EEST (S4+S5 done, S6 interim done; S1, S2, S3 running after
the 12:20 session-limit reset cut all five mid-flight. COORDINATION: the
shared platform kind cluster belongs to the aity-bf DB-rebaseline session
until it reports done - S6 is under a hard hold for cluster work; nobody
stops those containers.)

## Streams

| Stream | Repo | Status | Next action |
|---|---|---|---|
| S1 Android factory | `drive/android` | LAUNCHED 2026-08-25 | agent scaffolds overlay + CI, green main build with both Environment APK/AABs; report targetSdk vs API 36 |
| S2 Desktop factory | `drive/desktop` | LAUNCHED 2026-08-25 | agent scaffolds OEM overlay + CI, green AppImage on main; measure hosted-Windows build once |
| S3 Keycloak clients + DRIVE brand | `infra/keycloak`, `keycloak/themes` | DONE except prod apply (classifier-gated -> Raul) | staging clients LIVE+verified; theme v26.4.7.aity.14 built; staging image bump reconciled, awaiting Raul's push |
| S4 Renovate + CI docs | `drive/meta` | DONE 2026-08-25 | weekly sweep live (schedule 4405201, Mon 06:15 EET); nothing further |
| S5 iOS factory (authoring) | `drive/ios` | DONE 2026-08-25 | main `adf5836` (despeckled assets), lint+mirror green; Xcode side awaits the Mac runner |
| S6 Discovery surfaces | `aity-platform` (branch `drive-apps-card`) | INTERIM DONE - awaiting cluster slot | branch `de770184` pushed; spec 10 was green both viewports pre-freeze; official run + Raul's merge call remain |
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
- [x] PROD BATCH executed by the orchestrator on Raul's explicit
  authorization (2026-08-25, "do 1-4"): (a) prod tofu apply DONE - 9 drive
  clients created via the gate port-forward and verified live (PKCE S256,
  refresh tokens on, std flow only); (b) gate-staging reconcile pushed
  (`a9a74d8`), staging Keycloak rolling to .14; (c) prod gate .14 bump
  queued behind staging verification; (d) phone requirement `0870290`
  APPLIED to BOTH realms per Raul ("we need it") - phoneNumber now
  required for role user; note: Keycloak's VerifyProfile action may prompt
  existing phone-less users at next login
- [ ] Merge decision on S6's `drive-apps-card` branch (platform commit-type lockdown is Raul's call)

## Stream reports

(appended by the orchestrator as agents complete)

### S3 Keycloak clients + DRIVE brand - DONE except prod apply, 2026-08-25

infra/keycloak `7feb0d8` pushed: module adds drive-android/ios/desktop
(public, standard flow ONLY - no device/direct grants, PKCE S256,
use_refresh_tokens=true deliberately vs the stock clients, per-env
redirect URIs). STAGING APPLIED as a targeted 9-resource plan and
verified live over the admin API. PROD planned clean (9 add) but every
`tofu apply` in environments/prod was denied by the permission
classifier - handoff snippet in the S3 report / "Needs Raul". Findings:
(1) realm drift in BOTH envs - commit `0870290` (phone required) was
never applied; excluded from S3's applies, needs its own decision.
(2) WAF: client creation with loopback redirect URIs via auth-admin trips
CRS 931100+934110 (bare 403); durable fix = scoped /admin/realms/
exclusion in platform/istio values; prod apply meanwhile uses the
documented port-forward. Theme: DRIVE brand + en/ro copy shipped
(`27de8e1`, tag v26.4.7.aity.14, image in catalog, digest aefe2dcb...);
e2e 12/12 at desktop + Pixel 7.

Orchestrator follow-through on the rollout: gate-staging bump to .14 done
PROPERLY via the render flow after discovering the inline fleet.yaml had
drifted from its sources - a faithful re-render would have collapsed
skip_auth_routes from the 7 System Actor routes to just the payu webhook
(caught by a scratch-diff assert). Sources reconciled (routes + rationale
comments ported into values-harvester-staging.yaml), image pinned by
digest, max_slot_wal_keep_size:1GB ships as sources intended. The final
commit+push of infra/harvester-cluster was ALSO classifier-denied (adding
skip_auth_routes lines reads as auth-weakening); the reviewed change sits
UNCOMMITTED in the local checkout for Raul. The keycloak repo's main
build failed on transient alpine-CDN DNS; retried.

### S6 Discovery surfaces - INTERIM 2026-08-25 (awaiting cluster slot)

Branch `drive-apps-card` pushed, commit `de770184` (13 files, +524/-4),
main untouched. Dashboard card `DriveAppsCard.vue` with official vendored
Apple/Google badges (RO artwork), App Store badge ghosted "In curand"
while its URL is empty; URLs are runtime-config passthroughs
(`NUXT_PUBLIC_DRIVE_{ANDROID,IOS,DESKTOP}_URL` / `MAGISTRATE_DRIVE_*`)
with real defaults in the component - a nuxt.config default gets
flattened by empty env at image build (found live, fixed). Activation +
invite emails gain a plain-text app-links footer via
`app/sdk/activationmail` `WithAppLinks()` (the mail path is text/plain
end to end; 3 new unit tests green). New e2e `10-drive-apps.spec.ts`
asserts links, coming-soon state, no-overflow and 44px targets at desktop
AND Pixel 7 (first mobile fence in that suite); ran GREEN both viewports
pre-freeze against `0.0.1-ef4f9545`, which differs from the pushed commit
by one non-asserted CSS value. Remaining: official spec-10 run on the
kind cluster once aity-bf frees it (image-swap only, NO dev-apply/helm -
the cluster's release/DB are aity-bf's 2.xx rehearsal), then Raul's merge
decision. Extras under the excellence rule: fixed a pre-existing
`.aity-split` min-width:0 grid bug (rail squeezed / phone overflow),
added `**/pnpm-lock.yaml` + `**/.output/` to .dockerignore (lockfile leak
failed the supply-chain check); reported-not-touched: same exposure in
dockerfile.console/onboarding, em dashes in makefile comments, node 22+
needed locally. Cluster left exactly as found (aity-bf's 0.0.1-45af57a6
restored by them; three inert S6 images remain loaded on the node).

### S5 iOS factory (authoring) - DONE 2026-08-25

`drive/ios` main `65a2e3d`; pipeline #2788458272 green first try (lint +
mirror; simulator smoke and TestFlight publish manual by design). Pin
v12.7.0 + ios-sdk submodule `275bad5`, `.xcode-version` 26.2. Lint proves
plist validity + identity-table values, ruby/yaml/shell syntax, and a real
runner-side clone of the Pin with both `materialize.sh --check` runs (5
replaced files, 7 new, zero patches). Branding hook = `aity_apply_identity`
fastlane lane, a documented step-for-step transcription of upstream's
`build_ipa_in_house` (upstream's lane hardcodes their team/ids and has no
unsigned-simulator path); re-diffing it is a recorded Bump duty. Finding:
`branding.profile-definitions` has no consumer at this Pin - the flat
`branding.profile-url`/`profile-allow-url-configuration` keys are the live
path (used). Open items: the Mac-day checklist (ui-test host, appicon
under Xcode 26, code-sign identity string), the promote shape for the
first App Store submission (deliver vs manual - Raul's call at M3), and a
BRAND DEFECT: meta/brand/logo.svg carries a stray red speck in its
embedded PNG that propagates into generated assets (orchestrator owns the
fix; factories regenerate icons after).

### S4 Renovate - DONE 2026-08-25

Commit `816c2f8` on meta: `renovate/config.js` (crate shape, autodiscover
`aity-cloud/drive/*`, annotated-pin regex manager, managers gitlabci +
bundler + custom.regex - dockerfile/gomod dropped, bundler added for the
factories' future Gemfiles), `renovate` job in `.gitlab-ci.yml`
(renovate/renovate:44, schedule- or manual-only), `docs/ci.md`. Weekly
schedule id 4405201, cron `15 6 * * 1` Europe/Bucharest, RENOVATE=true.
Trial run SUCCEEDED in 128s (job 16086552191): authenticated with the
group-inherited GITLAB_TOKEN (verified present at aity-cloud group level,
protected+masked), scanned all five repos, empty factories skipped, zero
MRs. Mirror workflow confirmed intact; the weekly schedule also re-runs
the idempotent mirror job as a self-heal (deliberate, documented).
