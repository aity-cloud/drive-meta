# Agent prompt: Tier 2 and Tier 3 end-to-end tests for the Aity Drive Clients

Hand everything below the line to an agent. Tier 1 (the server contract
test) is already built and green - see `contract/README.md`; do not
duplicate it.

---

You are building end-to-end tests for the Aity Drive Clients. Work
autonomously; ask only where this prompt says to. Your final text is a
report, not a chat message.

## Read first (in this order)

- `drive/meta/AGENTS.md` - subgroup rules, all binding
- `drive/meta/specs/aity-drive-v1.md` - identity table, Environment builds,
  pipeline shape
- `drive/meta/contract/README.md` + `contract/drive_contract.py` - Tier 1,
  which already covers the server side. Your tiers cover what it cannot:
  what the CLIENT does with a correct server.
- `drive/ios/MAINTAINING.md` and `drive/desktop/MAINTAINING.md` - every trap
  these factories have actually hit. Read them before theorising about a
  failure; several are non-obvious (Icon Composer beating the icon set,
  the debrand pass skipping its own tree, `xcodebuild | tee` blowing the
  4 MB job-log cap).

## Context you need

- The `macos` GitLab runner is Raul's MacBook Air (transitional), tagged
  `macos`, protected refs only, one job at a time. It is shared hardware:
  never queue long jobs speculatively, and keep every Xcode job `when:
  manual` unless told otherwise.
- Staging is `https://drive.aity.works` (realm `https://auth.aity.works/realms/aity`).
  Test credentials are the protected group variables `AITY_CONTRACT_USER`
  and `AITY_CONTRACT_PASSWORD` on `aity-cloud/drive`. That account is
  `drive-contract@aity.works` with the `ocisUser` role.
- Builds are signed with `match` (reproducible profiles in the private
  `certificates` repo). Team ID `Z3C9R3AHZ8`.

## Tier 2 - iOS UI test (do this first, it has the most value)

Goal: a test that proves the app **opens an account and lists files**, not
just that it launches. The current `smoke:simulator` only checks the login
screen renders.

Target journey, on the simulator, against staging:

1. Launch the staging build.
2. Sign in as the contract user.
3. Assert the file list for the personal space appears.
4. Upload or create a file from the app if the UI allows it, assert it
   appears, then remove it (leave no litter - the workspace has a standing
   staging-hygiene rule).

The hard part is step 2: login is OIDC through a system browser sheet
(`ASWebAuthenticationSession`). XCUITest can drive it, but it is the
flakiest thing in mobile testing. Investigate, in this order, and pick with
reasons:

- Whether upstream's own UI tests in the Pin already solve it (the
  materialised tree at `drive/ios/build/upstream` has upstream's test
  targets - read them; reusing their harness is cheaper than inventing one
  and it tells us when a Bump breaks something upstream tests).
- Whether the app's `branding.profile-*` keys or `bookmark.prepopulation`
  can pre-seed an account so the test skips interactive login. Check
  `doc/configuration.adoc` in the materialised tree for what the Pin
  actually supports - do not trust blog posts.
- Only then, driving the browser sheet directly.

Deliverables: the test in `drive/ios` (extend `smoke/`), a CI job that runs
it on the `macos` runner, `MAINTAINING.md` updated with what you learned,
and an honest statement of flakiness (run it at least 3 times and report
pass rate; a test that fails 1-in-3 is worse than no test and should be
marked `allow_failure` until stabilised).

## Tier 2b - Android

Same journey with Espresso/UI Automator on an emulator. The Android factory
already has a `smoke:emulator` job that deliberately **fails** as a
placeholder (`exit 1` so it cannot fake a green smoke) - replace it with a
real instrumented test. The emulator runs on the same Mac runner (Apple
Silicon system image). Android's login is a Custom Tab, with the same
interactive-OIDC problem; the Android factory's `setup.xml` has
`oauth2_*` keys worth reading first.

## Tier 3 - desktop

Read `drive/desktop/MAINTAINING.md` "Sync smoke gap" before starting: at
this Pin `owncloudcmd` is gone and the GUI is OIDC-only, which is why the
`smoke:sync` job is a `when: never` skeleton. Your job is to determine
whether that is still true and, if so, what the cheapest honest option is.
Investigate:

- Whether the Pin ships any headless/CLI entry point (check the built
  AppImage's contents, not just docs).
- Whether upstream's own GUI test harness is usable without a licensed
  tool.
- Whether a sync round trip can be driven by seeding the client's config +
  a token, so the GUI never has to be automated.

If none of these is viable, say so plainly and stop - do NOT build a
brittle screen-scraping harness. Document the finding in
`drive/desktop/MAINTAINING.md` so the next person does not re-investigate.
A well-argued "not worth it, here is why, revisit when upstream ships a
CLI" is an acceptable and valuable outcome.

## Rules for all of it

- Tests assert BEHAVIOUR, not implementation details. "The file list shows
  the file I uploaded" is a test; "a private method returned 200" is not.
- No test may leave anything behind on staging.
- Never commit credentials. Everything comes from protected CI variables.
- Both Environment builds exist for a reason: test against **staging**,
  never production.
- If a test finds a real bug, that is a success - report it with the
  evidence (logs, request traces) rather than working around it.
- Commit identity `raul@aity.ro`; plain dashes only, never em dashes;
  AGENTS.md is canonical and CLAUDE.md is a symlink to it.

## Report

For each tier: what you built, where it runs, its measured pass rate, what
it does NOT cover, and any bug it found. Be explicit about anything you
could not verify.
