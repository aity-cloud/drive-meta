# Agent rules for the drive subgroup

This is the meta repo for `gitlab.com/aity-cloud/drive`: the Aity Drive
Clients - the branded ownCloud Android, iOS and desktop apps. Read
`specs/aity-drive-v1.md` before doing anything; `CONTEXT.md` holds the
vocabulary; `docs/adr/` holds the decisions with their why;
`docs/maintenance.md` is the standing loop.

## Rules - always, no exceptions

- **Overlay only (ADR 0001).** A Factory repo holds the Pin, the Branding,
  the Patches and CI. Never a copy of the upstream tree. Anything Branding
  can express is Branding; a Patch needs "not shippable without it" and an
  entry in that repo's `PATCHES.md`. Zero Patches is the target.
- **Upstream trademark stays out of our names.** No "owncloud" in group,
  repo, package, bundle or product names; "ownCloud" in prose about the
  upstream software is fine, and the GPL notices and copyright lines
  inside the apps are never removed.
- **CI publishes, humans promote.** Every artifact (APK/AAB, IPA, MSI/PKG/
  AppImage, source tarball, update feed) is built and uploaded by the tag
  pipeline. Nothing is built, signed or uploaded from a workstation. The
  manual `promote` job is the only path to a public listing.
- **Both Environment builds, always.** A release that does not produce the
  staging build is not a release; staging is verified before promote.
- **Secrets never enter a Factory.** Repos are mirrored verbatim to public
  GitHub (ADR 0004). Signing material lives in protected CI variables and
  the private `certificates` repo only.
- **The Public Mirror is a consumer.** Never push to it by hand, never
  build from it, never open MRs there.
- **Response targets are binding** (`docs/maintenance.md`): security
  release promoted within 3 business days, regular within 2 weeks, never
  more than one upstream minor behind.
- **Discovery surfaces are UI**: the Magistrate card, the email footers and
  the web links follow the workspace mobile-readiness rule (checked at a
  phone viewport, e2e at a phone viewport).
- **AGENTS.md is canonical; CLAUDE.md is a symlink to it** in every repo of
  the subgroup. Commit identity is `raul@aity.ro`.
- **Em dashes never appear in files or commits**; use plain dashes.
