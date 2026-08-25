# Aity Drive Clients v1 - specification

Status: grilled with Raul on 2026-08-25; all 18 decisions below are final. Vocabulary: `../CONTEXT.md`. Reasons: `../docs/adr/`.

## Goal

Ship Aity-branded, preconfigured Drive apps - Android and iOS in the
stores, desktop for Windows/macOS/Linux as direct downloads - built only by
GitLab CI from the upstream ownCloud clients, maintainable as a small
Overlay per Client, licence-compliant, and verified on staging before every
promotion.

## Non-goals (v1)

- Aity-specific features in any Client (white-label only).
- Microsoft Store / Mac App Store / F-Droid listings.
- MDM/AppConfig profiles beyond what upstream Branding already exposes.
- Telemetry or crash-reporting SDKs of any kind.
- Replacing the Web Client's theme mechanism (stays on oCIS + drive-theme).

## Decisions

| # | Decision | Where recorded |
|---|---|---|
| 1 | All three Clients in v1; white-label only | this spec |
| 2 | Overlay factories, not forks | ADR 0001 |
| 3 | Subgroup `aity-cloud/drive/` with `meta`, `android`, `ios`, `desktop` | ADR 0002 |
| 4 | Own identity: `tech.aity.drive`, `aitydrive://`, new KC clients `drive-android|ios|desktop`; stock IDs retired after launch | identity table |
| 5 | Two Environment builds per Client (staging + production), side-by-side installable | channels table |
| 6 | Publisher = AITY CLOUD SRL as an organisation on Apple, Google, Azure Trusted Signing | store section |
| 7 | Secrets: GitLab protected variables + fastlane match (`drive/certificates`) + Azure Trusted Signing; Play App Signing | CI section |
| 8 | Tags `v<upstream>-aity-<n>`; store version = upstream version; build number = `CI_PIPELINE_IID` | versioning |
| 9 | iOS ships on the App Store under GPLv3, like OpenCloud | ADR 0003 |
| 10 | Complete source of every release on the Public Mirror, GitHub org `aity-cloud` | ADR 0004 |
| 11 | Runners: self-managed Mac (`macos`), GitLab-hosted Windows, existing Linux group runner | ADR 0005 |
| 12 | Desktop installers + update feeds on the Public Mirror's GitHub Releases/Pages; updater ON | distribution |
| 13 | Tag pipeline auto-publishes staging builds to internal tracks; manual `promote` | pipeline |
| 14 | Renovate watch from `meta` + response targets | `docs/maintenance.md` |
| 15 | Client defaults bundle (below) | defaults |
| 16 | Discovery: Magistrate card, Drive web links, activation/invite emails, aity.ro page | discovery |
| 17 | App Review demo account: dedicated user in Aity's own production workspace | store section |
| 18 | Keycloak login theme gets its own DRIVE brand (wordmark AITY DRIVE), mapped from clientId prefix `drive` | follow-along fixes |

## Repositories

```
gitlab.com/aity-cloud/drive/
  meta/          this repo: CONTEXT.md, docs/adr, specs, docs/maintenance.md,
                 renovate/config.js, brand/ (master logo SVG, palette, icon
                 generation script)
  android/       Factory: Pin owncloud/android
  ios/           Factory: Pin owncloud/ios-app (+ ios-sdk submodule at the Pin)
  desktop/       Factory: Pin owncloud/client
  certificates/  private, fastlane match store (Apple certs + profiles)
```

Local checkout: `~/Documents/projects/aity/drive/{meta,android,ios,desktop}`
(the workspace `AGENTS.md` gains a `drive/` entry).

### Factory layout (identical shape in all three)

```
.gitlab-ci.yml        UPSTREAM_TAG pin (renovate-annotated), stages below
UPSTREAM.md           what the Pin is, how to Bump
PATCHES.md            hunk-by-hunk inventory of patches/ (empty is the goal)
MAINTAINING.md        traps this Factory has actually hit
overlay/              Branding files copied over the materialised tree
  production/         per-Environment values (server URL, ids, schemes)
  staging/
  common/             assets, colours, strings, feature flags
patches/              *.patch applied after the overlay
scripts/materialize.sh  clone Pin -> apply overlay/<env> -> apply patches
                        (same script CI and a developer use)
fastlane/             ios + android only: lanes for build, smoke, tracks
```

Public GitHub mirrors (ADR 0004): `aity-cloud/drive-android`,
`drive-ios`, `drive-desktop`, `drive-meta`, push-mirrored from GitLab.
The stale full fork `aity-tech/drive-desktop` (0 ahead / 360 behind
upstream, no Aity commits) is archived with a README pointer.

## Identity

| | Android | iOS | Desktop |
|---|---|---|---|
| Upstream Pin (at grill time) | `owncloud/android` v4.8.3 | `owncloud/ios-app` v12.7.0 (`ios-sdk` as submodule) | `owncloud/client` v7.1.0 |
| Licence | GPLv2 | GPLv3 (ADR 0003) | GPL-2.0-or-later |
| App name | Aity Drive | Aity Drive | Aity Drive |
| Production id | `tech.aity.drive` | `tech.aity.drive` + `.fileprovider`, `.fileprovider-ui`, `.intents`, `.share`, `.action`; app group `group.tech.aity.drive` | `APPLICATION_REV_DOMAIN tech.aity.drive`, shortname `aitydrive`, executable `aity-drive` |
| Staging id | `tech.aity.drive.staging` | `tech.aity.drive.staging` (+ same suffixes, group `group.tech.aity.drive.staging`) | shortname `aitydrive-staging`, name "Aity Drive (staging)", own config dir |
| macOS app group | - | - | `<TEAMID>.tech.aity.drive` (`.staging`): macOS 15+ requires Team-ID-prefixed groups or a Developer ID provisioning profile; the Factory ships both |
| Redirect (prod) | `aitydrive://android.aity.tech` | `aitydrive://ios.aity.tech` | `http://127.0.0.1:*`, `http://localhost:*` |
| Redirect (staging) | `aitydrive-staging://android.aity.works` | `aitydrive-staging://ios.aity.works` | same loopback |
| Keycloak client (per realm) | `drive-android` | `drive-ios` | `drive-desktop` |
| Branding mechanism | `setup.xml` (+ one-line gradle `applicationId` patch) | `Branding.plist` + `branding-assets/` + fastlane | `OEM_THEME_DIR` with `OEM.cmake` + `Theme` subclass + icons |

Keycloak (tofu, `infra/keycloak` `aity-realm` module, both environments):
three public clients, standard flow only, PKCE S256 required, no client
secret, redirect URIs and web origins as above, default scopes = the
existing `owncloud_default_scopes` (adds `owncloudUUID`, `ownCloudRoles`),
`offline_access` optional. Verify refresh-token behaviour explicitly: the
stock clients are registered with `use_refresh_tokens = false`, which is
almost certainly wrong for mobile apps that request `offline_access`;
the new clients must keep a user signed in across access-token expiry.
The three stock ownCloud clients stay until the branded apps are promoted,
then are removed in one tofu change.

## Environments and channels

| Environment build | Server | Keycloak | Android | iOS | Desktop |
|---|---|---|---|---|---|
| staging | `drive.aity.works` | `auth.aity.works` | Play internal testing | TestFlight internal group | GitHub pre-release on the mirror (marked staging) |
| production | `drive.aity.tech` | `auth.aity.tech` | Play production (after promote) | App Store (after promote + review) | GitHub Release + update feeds (after promote) |

Both builds come from the same tag and the same Pin; the icon of the
staging build carries a visible badge.

## Versioning

- Tag: `v<upstream>-aity-<n>` per Factory (`v4.8.3-aity-1`); `<n>` resets
  to 1 on every Pin move and increments for Overlay-only re-releases.
- Store version string: the upstream version (`4.8.3`); `-aity-<n>` shown
  in the About screen only.
- Build number (`versionCode`, `CFBundleVersion`, desktop build id):
  `CI_PIPELINE_IID`, monotonic per Factory.

## Pipeline (per Factory)

```
materialize -> build -> smoke -> publish-staging -> promote (manual) -> mirror
```

- **materialize**: `scripts/materialize.sh <env>` for both Environments;
  fails if a Patch does not apply.
- **build**: Android AAB (+APK for the emulator smoke) on the Linux group
  runner (`docker, shared`); iOS IPA on the `macos` runner (Xcode per the
  Pin's `.xcode-version`, fastlane match + gym); desktop: AppImage on Linux
  (Craft container), PKG/DMG on `macos` (Craft, Developer ID signing +
  notarisation, Sparkle), MSI/EXE on `saas-windows-medium-amd64` (Craft,
  Azure Trusted Signing). Windows and macOS jobs run on tags and manual
  triggers only, never on every push (minutes and Mac time).
- **smoke** (against `drive.aity.works` with a dedicated staging smoke
  user): desktop `owncloudcmd` sync round-trip on Linux; iOS XCUITest login
  + list + upload on the Mac's simulator; Android instrumented login +
  list + upload on an emulator on the Mac runner (Apple Silicon system
  image). Any red smoke stops the pipeline before publish-staging.
- **publish-staging**: staging builds to Play internal / TestFlight
  internal / GitHub pre-release; production builds kept as pipeline
  artifacts.
- **promote** (manual, protected tags only): production builds to Play
  production, App Store submission, GitHub Release (installers, source
  tarball) and regenerated update feeds on the mirror's Pages.
- **mirror**: the `mirror:github` job from `meta/ci/mirror.yml` (included
  by every repo of the subgroup) pushes `main` + tags to the GitHub twin
  over SSH with a per-repo write deploy key held as the protected file
  variable `GITHUB_MIRROR_KEY` (minted by `meta/scripts/mint-mirror-keys.sh`).
  No PAT, no user identity, one key per repo, rotation = re-run the script.
  CI is the only writer of the mirror (ADR 0004).

Secrets (protected + masked, tag-protected refs only): Android upload
keystore (file variable) + passwords, Play service-account JSON, App Store
Connect API key, `MATCH_PASSWORD` + deploy key for `certificates`, Azure
Trusted Signing service-principal secret, GitHub token for mirror and
releases. GitLab "secure files" may replace file variables for keystores
and profiles if it proves cleaner; either way nothing lands in a repo.

Known risk: the hosted Windows runner is 2 vCPU / 7.5 GB; a Craft/Qt
build may be slow enough to matter. Measure on the first build; the
fallback is a Windows Server VM on Harvester registered as `windows`.

## Client defaults (decision 15)

| Area | Setting |
|---|---|
| Server | locked to the Environment's Drive URL; URL field hidden (`show_server_url_input=false`, `branding.profile-allow-url-configuration=false`, `overrideServerUrl()`) |
| Auth | OIDC only (`enforce_oidc`, `connection.allowed-authentication-methods`), PKCE, no client secret, scopes as the KC clients define |
| Accounts | multi-account allowed |
| Lock | passcode/biometrics available, not enforced |
| Network | secure connection enforced; screenshots allowed |
| Links | help `https://aity.ro/contacteaza-ne/` (no support page exists on aity.tech yet); privacy `https://aity.tech/documents/privacy/`; terms `https://aity.tech/documents/terms/`; imprint AITY CLOUD SRL, CUI 39458128 |
| Upstream extras | feedback, release notes, in-app news off; iOS `DISABLE_APPSTORE_LICENSING`; desktop `CRASHREPORTER_SUBMIT_URL` empty |
| Telemetry | none; store-provided crash statistics only |
| Desktop | updater on (`APPLICATION_UPDATE_URL` -> mirror Pages feeds); virtual files at upstream default |
| Colours | brand red-600 `#B80818` family from `meta/brand/` (same palette as aity-ds.css and the drive-theme) |

## Store presence

- Accounts (none exist today): Apple Developer Program as an organisation
  (D-U-N-S for AITY CLOUD SRL, 99 USD/yr, also covers Developer ID for
  macOS), Google Play Console organisation (D-U-N-S, 25 USD once; the
  12-tester closed-test rule applies to personal accounts only), Azure
  Trusted Signing for Windows. Enrolment lead time is the critical path -
  start on day one.
- Listing metadata (descriptions, screenshots, privacy labels / data
  safety) lives in each Factory under `fastlane/metadata` and is pushed by
  CI; privacy policy URL `https://aity.tech/documents/privacy/`.
- App Review demo account (decision 17): a permanent `appreview@<Aity's
  own workspace domain>` workspace identity (assumed `aity.ro`; confirm at
  enactment) in AITY CLOUD SRL's own organisation on production, `ocisUser`
  role, a handful of sample files in its personal space, no admin roles.
  Password rotated after every review and kept only in the store review
  notes; never a customer's identity, never a special code path.
- iOS licence stance: ADR 0003; GPL notices and a source link in About.

## Discovery (decision 16)

- Magistrate index page: a "Get Aity Drive on your devices" card with
  App Store / Google Play badges and desktop download links; mobile-ready,
  e2e at a phone viewport (aity-platform).
- Drive web: fill `clients.android/ios/desktop` in the drive-theme config
  with the listings/Releases.
- Activation and invite emails: an "install the apps" footer (aity-platform
  notification templates).
- aity.ro `/aity-workspace/`: store badges (WordPress, outside the repos).

## Follow-along fixes found during the grill

- Keycloak login theme: `keycloak/themes/src/aity/brand.ts` maps only
  `magistrate*`/`mail*` to the MAIL brand; the `drive` client and the new
  `drive-*` clients fall through to the CLOUD panel. Decision 18: add a
  DRIVE Brand entry (wordmark AITY DRIVE, product "Aity Drive", own
  title/subtitle/bullet i18n keys) resolved from the clientId prefix
  `drive`, with e2e at desktop and phone viewports; ships with M4 but fixes
  the existing web login as soon as it lands.
- `aity-tech/drive-desktop`: archive (see Repositories).
- Observation, out of scope: the Web theme is cloned from GitHub at pod
  start (`aity-tech/drive-theme`), a runtime dependency on GitHub outside
  GitLab; worth moving under a Factory later.

## Risks and assumptions

- Upstream bus factor (iOS effectively one developer). Contingency: the
  OpenCloud forks keep the same Branding hooks; a Pin can move there if
  ownCloud's clients stall - needs an oCIS 8 compatibility check first.
- Relicensing to Apache-2.0 announced by Kiteworks' OSPO: makes ADR 0003
  moot when it lands; nothing to do until then.
- Xcode 26.2 (`.xcode-version`) requires macOS 26 on the Mac runner.
- Hosted Windows runner size (above).
- No Apple/Google accounts yet; D-U-N-S and organisation verification can
  take weeks.
- Google Play requires new apps to target API 36 from 2026-08-31; the
  Android Pin's `targetSdk` is checked in S1 before the first upload.
- Windows signing can run on the Linux runner with Jsign against Azure
  Artifact Signing, keeping the hosted Windows job to build-only.

## Order of work

- **M0** accounts + hardware: D-U-N-S, Apple org enrolment, Play org
  account, Azure Trusted Signing (runbook: `docs/runbooks/publisher-accounts.md`);
  the `macos` runner - Raul's personal Mac as a transitional runner
  (`docs/runbooks/mac-runner.md`), replaced by a Mac mini later without
  any repo change; `drive/` subgroup, `meta`, `certificates` and the three
  empty factory repos; GitHub mirrors created and wired with per-repo
  write deploy keys, `mirror:github` verified end-to-end on meta (DONE
  2026-08-25).
- **M1** `android` Factory (Linux only, fastest to prove the Overlay
  model): Keycloak `drive-android` in staging, materialize + branding +
  gradle patch, smoke, Play internal. Then Keycloak prod + production
  listing.
- **M2** `desktop` Factory: AppImage first (Linux runner), then macOS
  (Mac runner) and Windows (hosted); update feeds; GitHub Releases.
- **M3** `ios` Factory: bundle ids + app group under the Apple team,
  match, Branding.plist, XCUITest smoke, TestFlight internal, App Store
  submission (ADR 0003).
- **M4** discovery surfaces + Keycloak brand fix + stock-client removal.
- **M5** Renovate in `meta`, maintenance loop live, first scheduled run.

## Parallel work streams (who can do what, now)

Every stream is a separate repo or a disjoint file set, so they can run
concurrently on different agents without merge conflicts. Shared truth is
this spec; a stream that needs a decision not in it stops and asks Raul.

| Stream | Scope (repo) | Can start | Blocked on | Hand-over artefact |
|---|---|---|---|---|
| **S1 Android factory** (M1) | `drive/android`: materialize script, `overlay/` (setup.xml, icons, strings, both Environments), the one-line `applicationId` patch, unit tests, `.gitlab-ci.yml` (materialize -> build AAB/APK -> smoke job tagged `macos` -> publish-staging -> promote -> mirror), `fastlane/` with `supply`, `PATCHES.md`, `MAINTAINING.md`, `UPSTREAM.md` | now | Play internal upload waits for the Play account + service account (M0); the emulator smoke waits for the `macos` runner; Keycloak `drive-android` from S3 for a real login | signed-config-free staging APK as a pipeline artefact |
| **S2 Desktop factory** (M2) | `drive/desktop`: `overlay/` as an `OEM_THEME_DIR` (`OEM.cmake`, `Theme` subclass, icons, both Environments), Craft blueprints/config, `.gitlab-ci.yml` with the Linux AppImage job (Linux runner), the Windows job (`saas-windows-medium-amd64`, unsigned until Azure Trusted Signing), the macOS job (tagged `macos`, unsigned until Developer ID), `owncloudcmd` smoke against staging, update-feed generator for GitHub Pages | now | Signing (M0); macOS job runs only once the `macos` runner exists | AppImage + unsigned Windows installer artefacts; measured Windows build time |
| **S3 Auth + login brand** (M4 auth part) | `infra/keycloak` tofu: `drive-android|ios|desktop` public PKCE clients in the `aity-realm` module (both environments) with the refresh-token check; `keycloak/themes`: DRIVE brand entry + i18n + e2e at desktop and phone viewports; stock-client removal prepared behind a flag | now | `tofu apply` needs Raul's VPN (staging first, prod after the apps are promoted) | tofu plan output for Raul; theme MR with green e2e |
| **S4 Meta automation** (M5 + mirror) | `drive/meta`: Renovate config (`autodiscoverFilter: ['aity-cloud/drive/*']`, github-tags watch on `UPSTREAM_TAG`), scheduled pipeline, `docs/ci.md`; verify `mirror:github` end-to-end once keys exist | now | mirror keys (GitHub org deploy-key setting) | weekly Renovate run producing Pin-watch MRs |
| **S5 iOS factory** (M3) | `drive/ios`: materialize (app + `ios-sdk` submodule at the Pin), `overlay/` (`Branding.plist`, `branding-assets/`, both Environments, six bundle ids + app group), `fastlane/` (match, gym, pilot, deliver, XCUITest smoke on the simulator), `.gitlab-ci.yml` with every job tagged `macos` | once the `macos` runner exists | Signing, TestFlight and App Store need the Apple org account (M0); simulator build + smoke need no account at all (`CODE_SIGNING_ALLOWED=NO`) | simulator smoke green on the Mac runner |
| **S6 Discovery surfaces** (M4 UI part) | `aity-platform`: Magistrate "Get Aity Drive" card (mobile-ready, phone-viewport e2e), activation/invite email footer; `aity-tech/drive-theme`: `clients.*` links; aity.ro badges | now, with config-driven URLs | real listing URLs after the first store submissions | MR with placeholder URLs behind config |
| **Raul** (M0) | publisher accounts per `docs/runbooks/publisher-accounts.md`, the `macos` runner per `docs/runbooks/mac-runner.md`, GitHub org deploy-key setting, VPN for tofu applies, buying GitLab minutes, every `promote` | now | - | accounts, runner online |

Ordering hints: S1 and S2 prove the Overlay model on the Linux runner
first; S3 is the prerequisite for any real login smoke in S1/S2/S5; S4 is
tiny and unblocks the public mirrors for everything else; S5 waits for the
Mac. Each stream ends with its `PATCHES.md` honest (ideally empty) and its
`MAINTAINING.md` recording what actually bit.

