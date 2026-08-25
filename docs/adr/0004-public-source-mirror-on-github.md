---
status: accepted
---

# Complete source of every Client release is published on GitHub

The Clients are GPL (Android GPLv2, desktop GPL-2.0-or-later, iOS GPLv3),
so every store or download distribution must make the complete corresponding
source available, and ADR 0003 leans on that availability. The Factories
live in the private `aity-cloud` GitLab group, whose visibility forbids
public projects. We decided that each Factory is push-mirrored by CI to a
public repository under the `aity-cloud` GitHub organisation
(`drive-android`, `drive-ios`, `drive-desktop`, `drive-meta`), and that
every release additionally publishes the materialised source tree (Pin with
Overlay and Patches applied) as a release asset there, so a recipient gets
buildable source without reconstructing it from a recipe. The in-app
licence screen links to that repository and release. GitHub, not a second
GitLab group, because the organisation already has a public GitHub presence
and the self-hosted runner stays bound to `aity-cloud` on GitLab.

## Considered options

- **Public factories in a new top-level GitLab group**: no mirror lag, but
  a second top-level group and a runner to re-register.
- **GPL "written offer" only**: compliant on paper, a support burden in
  practice, and it weakens the source-availability argument of ADR 0003.

## Consequences

- The mirror is a consumer: never pushed to by hand, never built from.
- Signing material and store credentials must never enter the Factory
  repos at all (they are mirrored verbatim); they live in protected CI
  variables and the private certificates repo.
