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

## Per-Bump checklist

1. Move `UPSTREAM_TAG`; read upstream's changelog for Branding-key changes
   (`setup.xml`, `Branding.plist` keys, `OEM.cmake` variables) - those are
   the only breaking changes an Overlay can see.
2. `patches/` applies cleanly; a Patch that no longer applies is either
   rebased with a note in `PATCHES.md` or dropped because upstream fixed it.
3. Materialise locally, open in the IDE once, confirm the branded login
   against `drive.aity.works`.
4. Tag. The pipeline builds both Environment builds, runs the smoke, and
   publishes the staging builds to the internal tracks.
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
