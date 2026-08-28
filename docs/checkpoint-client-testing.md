# Checkpoint: client testing still owed (saved 2026-08-28)

A resumable handoff for the Android / Windows / macOS work that is NOT
done, written so another session can pick it up cold. Status of everything
else is `execution.md`; the traps are in each Factory's `MAINTAINING.md`,
which must be read before theorising about any failure.

## Where each client actually stands

| Client | Builds | Tested how far | Blocked on |
|---|---|---|---|
| **iOS** | staging + prod, TestFlight **build 51** | Works on a real device (Raul, 2026-08-27). Simulator journey 5/5: sign in, open personal space, list, create folder, delete it | Beta App Review demo account, for external (friends-and-family) distribution |
| **Android** | debug-signed APK/AAB, both Environments | Emulator smoke 5/5 (`scripts/emulator-smoke.sh staging`, ~17s) | Play organisation account; upload keystore; the app has never run on a real phone |
| **Desktop, Linux** | branded AppImage, both Environments | Branding smoke only - launches, reports `aitydrive <version>`, correct desktop entry | A real sync round trip: no headless client at this Pin (see "Sync smoke gap") |
| **Desktop, macOS** | **never built** | nothing | `build:macos` has never run; Developer ID certificate not minted |
| **Desktop, Windows** | **never built** | nothing | `ci_quota_exceeded` - GitLab compute minutes; then Azure Artifact Signing |

## macOS - the next session's main job

Everything is written and waits on execution:

1. `match developer_id` mints the certificate. Developer ID is gated by
   ROLE (Account Holder), not membership type, so the individual Apple
   account can do it today - `fastlane/Fastfile` in `drive/desktop` has the
   `developer_id_certificate` lane.
2. Run `build:macos` (manual, `tags: [macos]`, 3h timeout). It has NEVER
   executed - expect iteration, and read `MAINTAINING.md` first.
3. `scripts/sign-macos.sh` already does codesign `--options runtime` +
   `notarytool submit --wait` + `stapler staple`, and skips loudly when
   credentials are absent rather than shipping something unsigned and
   quiet.
4. Publish: notarised DMG to the Public Mirror's GitHub Release, plus the
   per-OS update feeds from `scripts/gen-update-feeds.sh`.

Identity reminder: the macOS bundle id is `tech.aity.drive.desktop`
(`.desktop.staging`), deliberately NOT the iOS app's - both can sit on one
Apple Silicon Mac.

## Windows

`build:windows` fails instantly with `ci_quota_exceeded`; it is a hosted
`saas-windows-medium-amd64` job and Raul is buying minutes. Signing is
Azure Artifact Signing (the renamed Trusted Signing): EU organisations
eligible, 9.99 USD/month, identity validation 1-20 business days. A
cheaper path exists and is worth taking: **Jsign on the Linux runner**
against the same service, so the expensive Windows job only builds.

## Android

The emulator smoke passes; what is missing is an account and a device.
Play needs the organisation account (D-U-N-S), an upload keystore
(`ANDROID_UPLOAD_KEYSTORE*`) and `PLAY_SERVICE_ACCOUNT_JSON`; the publish
jobs are written and no-op loudly without them. Note the Pin already
targets **API 36**, so Google's 2026-08-31 deadline is satisfied.

Known upstream defect, do not re-investigate: a folder created in the app
has no Remove/Rename/Move until the list refreshes - owncloud/android
#4673, open since 2025-09-01, still open on our newest tag v4.8.3. Raul
decided: document, do not contact upstream, no patch.

## The gap that matters most

**No test covers a signed build.** The account-journey smoke runs on the
simulator, and identity changes made in the SIGNING lane never reach it -
which is exactly how the framework-rename crash shipped past a 5/5 green
suite and died on Raul's phone. Closing it means running the journey
against a signed build on a real device or via TestFlight. Until then,
treat "simulator green" as evidence about the code, never about the
shipped artifact.

## How to resume

Read `execution.md`, then this file, then the Factory's `MAINTAINING.md`.
Pre-flight before any Mac job: run meta's `client-auth:staging` (seconds on
Linux) - it proves the three OIDC clients still work and costs nothing,
which beats discovering a broken registration half an hour into a job on
Raul's laptop. The Mac runner is his MacBook Air: one job at a time, every
Xcode job `when: manual`, never queue speculatively.
