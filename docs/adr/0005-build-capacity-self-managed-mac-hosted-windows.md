---
status: accepted
---

# Build capacity: a self-managed Mac, GitLab-hosted Windows, our own Linux runner

Three Clients need three build platforms. The estate has one self-hosted
Linux group runner (`docker, shared`), GitLab is on the Free tier, and
GitLab's hosted macOS runners are Premium/Ultimate-only and Beta. We
decided: iOS and the macOS desktop build on a self-managed Apple Silicon
Mac registered as a `macos` group runner (shell executor as a user
LaunchAgent, so keychain, codesign and the simulator work); the Windows
desktop builds on GitLab's hosted Windows runners, paid for with purchased
compute minutes; Android and the Linux AppImage build on the existing Linux
runner. A Mac is a one-off purchase that works on every tier, while hosted
macOS would force a Premium subscription for a Beta pool; hosted Windows is
cheap (cost factor 1) and spares us a licensed Windows VM to keep patched.

## Considered options

- **Upgrade to Premium for hosted macOS**: no hardware, but a recurring
  per-user cost plus minute add-ons, documented queuing, and Beta status.
- **Windows Server VM on Harvester**: fully self-hosted, but a Windows
  licence and an OS to maintain for a job that runs a few times a month.

## Consequences

- The Mac is part of the release path: it needs the same patch, backup and
  monitoring discipline as the Linux runner, and Xcode upgrades follow the
  iOS Pin's `.xcode-version`.
- Windows builds consume purchased minutes; the pipeline must not run them
  on every push, only on tags and on demand.
