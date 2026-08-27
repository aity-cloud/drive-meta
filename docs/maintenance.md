# Maintenance loop for the Aity Drive Clients

The standing loop that keeps the three Factories (`android`, `ios`,
`desktop`) current with their Upstreams. Vocabulary in `CONTEXT.md`; the
reasons in `docs/adr/`.

## Upstream watch

- Each Factory keeps its Pin as an annotated CI variable, exactly like
  `crate/directpv`:

  ```yaml
  variables:
    # renovate: datasource=github-tags depName=owncloud/android
    UPSTREAM_TAG: "v4.8.3"
  ```

- Renovate CE runs weekly from this repo (`renovate/config.js`,
  `autodiscoverFilter: ['aity-cloud/drive/*']`, scheduled pipeline with
  `RENOVATE=true`), same job shape and token rules as `crate/meta`.
- A Renovate MR on `UPSTREAM_TAG` is a SIGNAL that upstream released, not a
  mergeable change. The Bump is a human act: read the upstream release
  notes, move the Pin, re-validate every Patch (drop the ones upstream
  absorbed), tag `v<upstream>-aity-1`, let the pipeline publish the staging
  Environment builds, verify on staging, promote.
- Renovate also proposes toolchain bumps in the Factories themselves (CI
  images, fastlane, gradle plugin) - those are ordinary MRs.

## Response targets

Clock starts when the signal lands (Renovate MR, upstream security advisory,
store policy notice).

| Finding | Target |
|---|---|
| Upstream security release, or a store policy deadline | Bump built, verified on staging and promoted within 3 business days |
| Regular upstream release | Bump promoted within 2 weeks |
| Standing rule | Never more than one upstream minor behind on any Client |
| Store metadata/policy change (privacy labels, target SDK, Xcode minimum) | Handled in the next Bump, or a `-aity-<n+1>` re-release if no Bump is due |

## The test tiers, and what each one is for

Four things run against a real Environment. Know which one to read when
something is red; they fail for very different reasons.

| Tier | Where | Runs on | Answers |
|---|---|---|---|
| 1 server contract | `meta/contract/drive_contract.py`, job `contract:staging` | Linux, every push + hourly schedule | is the SERVER still giving clients what they need? |
| 1.5 client auth | `meta/contract/drive_client_auth.py`, job `client-auth:staging` | Linux, every push + schedule | can each Client's OWN Keycloak client sign a user in, keep them signed in, and get a token oCIS accepts? |
| 2 iOS journey | `ios/smoke/AityDriveSmokeUITests`, job `smoke:simulator` | `macos`, manual | does the APP sign in, list the personal space, create and delete? |
| 2b Android journey | `android/overlay/common/owncloudApp/src/androidTest`, job `smoke:emulator` | `macos`, manual | the same, on Android |

There is deliberately no desktop sync smoke: `desktop/MAINTAINING.md`,
"Sync smoke gap", has the evidence and the conditions for revisiting it.

Run Tier 1 and 1.5 BEFORE triggering anything on the `macos` runner. They
take seconds on the Linux runner and they fail for the reasons a UI test
would otherwise take half an hour of Raul's laptop to discover.

Two facts both UI tiers depend on, so a change to either breaks both at once:

- the realm's browser flow is IDENTITY-FIRST (email page, then password
  page), and
- the login page is a React app (the Keycloakify `aity` theme), with no
  server-rendered form.

## Per-Bump checklist

1. Move `UPSTREAM_TAG`; read upstream's changelog for Branding-key changes
   (`setup.xml`, `Branding.plist` keys, `OEM.cmake` variables) - those are
   the only breaking changes an Overlay can see.
2. `patches/` applies cleanly; a Patch that no longer applies is either
   rebased with a note in `PATCHES.md` or dropped because upstream fixed it.
3. Materialise locally, open in the IDE once, confirm the branded login
   against `drive.aity.works`.
4. Tag. The pipeline builds both Environment builds, runs the smoke, and
   publishes the staging builds to the internal tracks. On iOS and Android
   the account-journey smoke is manual and shares one Mac, so trigger it
   deliberately and read `client-auth:staging` first.
5. Verify on staging (install from the internal track on a real device),
   then run the manual `promote` job.
6. Store-side: watch App Store review and Play pre-launch report; the
   Public Mirror release and update feeds are published by the same
   `promote` job.

## Platform hygiene that is part of this loop

- The Mac runner: macOS and Xcode follow the iOS Pin's `.xcode-version`;
  runner binary and fastlane kept current; Time Machine backup of the
  runner user's home is NOT a secret store - match and CI variables are.
- Certificates: Apple distribution certs expire yearly, provisioning
  profiles too; `fastlane match nuke`/`match` renewal is a calendar item.
  Android upload key never expires; Play App Signing holds the app key.
- Publisher accounts: Apple Developer Program renews yearly; Play requires
  periodic identity re-verification for organisation accounts.
