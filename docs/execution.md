# Aity Drive v1 - execution board

Living status of the multi-day, multi-agent build-out. SINGLE WRITER: the
orchestrator session updates this file; stream agents never push to meta.
The plan itself is `../specs/aity-drive-v1.md`; account steps are
`runbooks/publisher-accounts.md`; the Mac runner is `runbooks/mac-runner.md`.

Updated: 2026-08-25 14:4x EEST (S1, S2 Linux, S3 incl. prod, S4, S5 done; S6 rebased and awaiting the cluster slot - after
the 12:20 session-limit reset cut all five mid-flight. COORDINATION: the
shared platform kind cluster belongs to the aity-bf DB-rebaseline session
until it reports done - S6 is under a hard hold for cluster work; nobody
stops those containers.)

## Streams

| Stream | Repo | Status | Next action |
|---|---|---|---|
| S1 Android factory | `drive/android` | DONE 2026-08-25 | main `7bddf12` green; both Environment builds manifest-verified; targetSdk 36 already satisfied; 1 patch |
| S2 Desktop factory | `drive/desktop` | DONE (Linux path) 2026-08-25 | pipeline 2788769001 green: branded AppImages both Environments, smoke PASS, mirror live; zero patches; Windows waits on minutes, macOS on the Mac runner |
| S3 Keycloak clients + DRIVE brand | `infra/keycloak`, `keycloak/themes` | DONE 2026-08-25 | clients + phone requirement + .14 theme LIVE and verified in BOTH environments |
| S4 Renovate + CI docs | `drive/meta` | DONE 2026-08-25 | weekly sweep live (schedule 4405201, Mon 06:15 EET); nothing further |
| S5 iOS factory | `drive/ios` | BUILDS ON A REAL MAC 2026-08-27 | simulator smoke GREEN on the runner (job 16140937726); three factory bugs fixed; signing/TestFlight still needs the Apple team |
| S6 Discovery surfaces | `aity-platform` | DONE 2026-08-27 | merged to main (`de6f3521`); `10-drive-apps.spec.ts` GREEN at both viewports on the consolidated minikube stack, verified by the aity-6e session |
| Later | `drive-theme`, aity.ro | HELD | store links only when real listing URLs exist |
| Coordination | `infra/harvester-cluster` | FROZEN for us | aity-bf's staging/prod schema cutover in progress; no promotions (incl. the WAF exclusion) until they report done |

## Done

- [x] 18 decisions grilled; CONTEXT.md, ADRs 0001-0005, spec, maintenance loop (2026-08-25)
- [x] Subgroup `aity-cloud/drive`: meta, certificates, android, ios, desktop
- [x] GitHub mirrors wired (deploy keys + `GITHUB_MIRROR_KEY` + `ci/mirror.yml`), verified on meta
- [x] `aity-tech/drive-desktop` archived; workspace AGENTS.md lists `drive/`
- [x] Runbooks: publisher accounts, Mac runner

## Needs Raul (the only human steps)

- [x] D-U-N-S requested 2026-08-25; Apple is converting Raul's EXISTING individual developer account to an organisation once it lands (not a fresh enrolment)
- [ ] Apple Developer Program org enrolment + DSA trader + EU invoicing (runbook step 2)
- [ ] Google Play organisation account + verification (runbook step 3)
- [ ] Azure Artifact Signing identity validation (runbook step 4)
- [ ] Register the personal Mac as the `macos` group runner - PASTE-READY AGENT PROMPT: `docs/runbooks/mac-runner-agent-prompt.md` (hand it to Claude Code on the Mac; it creates the runner via the API, installs Xcode per the Pin, registers the LaunchAgent and proves it with a real job)
- [ ] TODO NEXT WEEK (Raul, 2026-08-25): buy GitLab compute minutes - S2's Windows build fails instantly with `ci_quota_exceeded`; everything else in S2 is green without it
- [x] PROD BATCH executed by the orchestrator on Raul's explicit
  authorization (2026-08-25, "do 1-4"): (a) prod tofu apply DONE - 9 drive
  clients created via the gate port-forward and verified live (PKCE S256,
  refresh tokens on, std flow only); (b) gate-staging reconcile pushed
  (`a9a74d8`), staging Keycloak rolling to .14; (c) prod gate .14 ROLLED OUT and verified (3/3 pods on the .14 digest, drive-android login page 200 with correct client context); (d) phone requirement `0870290`
  APPLIED to BOTH realms per Raul ("we need it") - phoneNumber now
  required for role user; note: Keycloak's VerifyProfile action may prompt
  existing phone-less users at next login
- [x] S6 branch MERGED to platform main 2026-08-25 on Raul's instruction (`de6f3521`, fast-forward, `fix:` type); cluster e2e was green pre-freeze at both viewports, the official post-rebase run is still owed when the kind cluster frees up

## NEW DEFECT found 2026-08-25 (needs Raul's call)

**Staging gateway WAF blocks desktop OIDC logins entirely**: any
`/realms/aity/protocol/openid-connect/auth` request with a loopback
`redirect_uri` (`http://127.0.0.1:*`) gets an empty istio-envoy 403 on
auth.aity.works - client-independent (stock ownCloud desktop id too);
PROD serves the same request 200. Same Coraza false-positive family S3
root-caused on the admin API (CRS 931100 RFI ip-url + 934110 SSRF
localhost-url), presumably a newer ruleset that staging runs first.
Consequences: S2's desktop smoke against staging cannot log in, and no
human can test the desktop client on staging. Proposed fix (NOT applied -
WAF loosening on an auth endpoint is Raul's decision): scoped exclusion
of those two rule ids for GET on that exact path on the staging gateway
in platform/istio values, mirroring the existing scoped /admin/realms/
exclusion pattern in gate TROUBLESHOOTING.md.

## First Mac-runner run - 2026-08-27

Raul registered his MacBook Air as the `macos` group runner (55598729,
darwin/arm64, protected, locked). The iOS simulator smoke went from
never-executed to GREEN in four iterations, each a real factory bug:

1. `ensure_xcode_version` needs the abandoned `xcode-install` gem, absent
   from the Pin's Gemfile - the lane died at the guard (`9a220fe`
   replaces it with a gem-free comparison).
2. `xcodebuild | tee` blew GitLab's 4 MB job-log cap, truncating the job
   before the error was visible - the log now goes to a file shipped as an
   artifact, with error lines printed on failure; the simulator build also
   stopped building both arm64 and x86_64 (`5c5e89a`).
3. THE REAL ONE: the Action Extension kept
   `com.owncloud.ios-app.ownCloud-Action-Extension` and Xcode refused the
   embedded binary. Every target takes its id from
   `PRODUCT_BUNDLE_IDENTIFIER`, and `update_app_identifier` decides by
   reading `CFBundleIdentifier` from the plist - which that extension's
   plist does not define at this Pin. The lane now sets the build setting
   per target and fails if a mapped target is missing (`c276f21`).

Green run proves for real: materialize, the whole identity transcription
(URL schemes, 7 target ids, app group, generated appicon), the unsigned
simulator build, `simctl install` of `tech.aity.drive.staging` and the
XCUITest smoke. Still unverified: everything signing (match, gym, pilot,
deliver, notarisation).

Android's `smoke:emulator` "failure" on the same runner is deliberate
scaffolding (exits 1 so it cannot fake a green smoke) until the
instrumented test exists.

## 2026-08-27 end of day

Both TestFlight apps are on **build 51**, processing VALID, and Raul
confirmed the staging app works on a real device.

Three defects fixed today, all found by the tests rather than by luck:

1. **oCIS 8 LDAP schema** - `ocLastSignInTimestamp` was undefined, so every
   sign-in threw and `/graph/v1.0/me` answered 500 intermittently.
   Production had been doing it ~17 times a day since the oCIS 8 upgrade.
   Applied to both directories by ldapmodify; init schema updated so a
   rebuild is born correct.
2. **Embedded framework rename** - our branding renamed
   ownCloudAppShared, upstream hardcodes and force-unwraps
   `Bundle(identifier: "com.owncloud.ownCloudAppShared")`, so every SIGNED
   build trapped seconds after an account connected. The simulator smoke
   could not see it: framework ids are rewritten in the signing lane, which
   simulator builds do not run. Frameworks keep upstream's ids now.
3. **Staging WAF** - the gateway 403'd every loopback OIDC redirect (prod's
   exception listed only ownCloud's stock ids; staging had no rule at all),
   so the desktop client could not sign in at all. Both gateways fixed,
   verified 403 -> 200, production unaffected.

Known gap, deliberately not closed: no test covers a SIGNED build. The
account-journey smoke runs on the simulator, and anything that only
happens in the signing path is invisible to it - which is exactly how
defect 2 shipped. Closing it means running the journey against a signed
build on a device or via TestFlight.

## Next: macOS (2026-08-28)

The desktop client's macOS path is the open work. Ready for it:
Developer ID is role-gated (Account Holder), not organisation-gated, so
the individual account can sign and notarise today; `scripts/sign-macos.sh`
already does codesign + notarytool + staple and skips loudly without
credentials; the certificate can be minted by `match developer_id`. Not yet
done: the Developer ID certificate itself, a first notarised DMG, the
GitHub Release + update feeds, and a run of `build:macos` on the Mac
runner (it has never executed).

## Stream reports

(appended by the orchestrator as agents complete)

### S2 Desktop factory - DONE (Linux path) 2026-08-25

`drive/desktop` main `25fcefc`; pipeline 2788769001: materialize:check,
build:appimage (796s, both Environments), smoke:appimage PASS (`aitydrive
7.1.0.5`, Qt 6.8.3, offscreen `--version`, desktop file "Aity Drive
desktop sync client"), mirror:github live. Pin v7.1.0. Branding is the
upstream OEM theme mechanism (`OEM_THEME_DIR` = `overlay/<env>` with
OEM.cmake + a Theme subclass + generated icons) - **zero patches**.
Update feeds: per-OS `APPLICATION_UPDATE_URL` branch in OEM.cmake +
`scripts/gen-update-feeds.sh` into `public/update/` (static Pages cannot
dispatch on the updater's query string, hence per-OS files). Sync smoke
against staging remains a documented gap (no headless client at the Pin;
`smoke:sync` skeleton `when: never`) - and staging's WAF would block the
loopback OIDC login anyway (see defect). The agent died in the session
limit before reporting; the orchestrator fixed the last red job (smoke
image lacked libOpenGL.so.0 + xcb runtime, MAINTAINING.md updated).
Remaining, externally gated: `build:windows` (failed instantly with
`ci_quota_exceeded` - buy minutes), `build:macos` (Mac runner),
`sign:windows` (Azure Artifact Signing).

### S1 Android factory - DONE 2026-08-25

`drive/android` main `7bddf12`; pipeline 2788480852 green (build 951s incl.
upstream unit tests), mirror live. Pin v4.8.3 - which already targets
API 36, so Play's 2026-08-31 requirement is satisfied as-is. Both
Environment builds produced and manifest-verified (aapt2 in-job + an
independent local parse): `tech.aity.drive` / "Aity Drive" /
`aitydrive://android.aity.tech` and the `.staging` twins; `drive-android`
client id, no secret; debug-signed until the upload keystore exists.
EXACTLY ONE Patch (applicationId/version wiring in owncloudApp/build.gradle
- AGP accepts these only from build scripts); everything else is resource
overrides in the `original` flavor source set, so Bumps conflict only on
that one hunk. Icons regenerated from the despeckled master (zero-diff
re-run proves it). MAINTAINING.md records real traps (JDK-17 pin for the
Pin's mockk, aapt2-based verification, ghcr android-sdk image over flaky
Docker Hub, scheme separation, two upstream "ownCloud" string leaks
handled). BRAND TODO surfaced: meta/brand/logo.svg is a 188px raster in
SVG clothing - xxxhdpi Android assets are soft at 432px; a true vector
master is wanted before store screenshots. Unblocks: keystore + Play vars
(M0), macos runner (emulator smoke), a device login against the now-live
drive-android clients, Play listing images.

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
