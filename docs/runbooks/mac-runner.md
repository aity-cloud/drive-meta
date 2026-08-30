# Runbook: the `macos` GitLab runner

The Mac that builds iOS and the macOS desktop client (ADR 0005). Until the
dedicated Mac mini arrives, Raul's personal Mac plays this role - accepted
on 2026-08-25 as a TRANSITIONAL state with the guard-rails below. The
runner is registered TWICE on the same Mac (one config.toml, two
`[[runners]]` entries): as a group runner of `aity-cloud/drive` (55598729,
the original) and, since 2026-08-30, as a group runner of the TOP group
`aity-cloud` (55705923) so projects outside the drive subgroup - `abm/ios`
first - can build on it. Both tagged `macos`, protected refs only, tagged
jobs only. New registrations go to the top group: a group runner is never
visible to a sibling subgroup, which cost abm/ios its first compile.

## Why a personal Mac is acceptable for now, and what makes it so

- Jobs run only on protected refs (tags and `main`) of the drive subgroup,
  so nothing an MR author writes can execute on the machine.
- Signing material never touches the login keychain: every job creates a
  temporary keychain (`fastlane setup_ci` / `create_keychain`), match
  installs into it, and the job deletes it. The runner user's own keychain
  stays untouched.
- The machine being asleep or away only delays a pipeline; `promote` is
  manual anyway and the same person is the one promoting.
- Xcode is selected per job with `DEVELOPER_DIR`, so the version the Pin
  needs (`.xcode-version`, currently 26.2) coexists with whatever else is
  installed (`xcodes` manages several versions side by side).
- What it does NOT give: an always-on release path, a clean machine for
  release builds, and separation from personal data. That is why the Mac
  mini remains the target, and why nothing in the pipelines may assume
  anything about the host beyond the tools listed here.

## One-time setup (about 30 minutes)

1. Create the runner in GitLab: group `aity-cloud` (the TOP group, so every
   subgroup can use it) -> Build -> Runners -> New group runner: tags
   `macos`, untick "Run untagged jobs", tick "Protected" (only protected
   branches/tags). Copy the `glrt-...` authentication token; it is shown
   once. (API equivalent: `POST /user/runners` with `runner_type=group_type`
   as an owner; agents are classifier-blocked from it.)
2. On the Mac:

   ```sh
   brew install gitlab-runner xcodes
   xcodes install 26.2 --select        # or whatever the iOS Pin's .xcode-version says
   sudo xcodebuild -license accept
   gitlab-runner register --non-interactive \
     --url https://gitlab.com --token glrt-REDACTED \
     --executor shell --description "raul-mac (transitional)" \
     --shell bash
   gitlab-runner install    # LaunchAgent in THIS user session (needed for codesign + simulator)
   gitlab-runner start
   gitlab-runner verify
   ```

   Run the install/start as the login user, never `sudo`: a LaunchDaemon
   has no GUI session and codesign/simulator fail from it.
   `--shell` MUST be `bash` (or omitted): gitlab-runner's shell executor
   knows bash, sh and powershell only. A registration with `--shell zsh`
   fails EVERY job at preparation with `shell zsh not found`, and because a
   top-group runner also serves drive, it drags drive's macos jobs down
   with it until fixed (2026-08-30).
   The Mac has no SSH path from anywhere: host-side chores after the first
   registration run as manual jobs of `aity-cloud/drive/mac-runner-ops`,
   executed by the drive runner itself (shell executor, login user). That is
   how the second registration and its shell fix were done.
3. Tooling the jobs expect on the host (everything else comes from the
   Factory's `Gemfile`/`Brewfile` at job time):
   - Xcode per the Pin, iOS simulator runtime matching it, Command Line Tools
   - `ruby` via Homebrew + `bundler` (fastlane runs through `bundle exec`)
   - Android: `brew install --cask android-commandlinetools`, then
     `sdkmanager "platform-tools" "emulator" "system-images;android-35;google_apis;arm64-v8a"`,
     `ANDROID_HOME` exported in the runner's shell profile (the Android
     smoke runs its emulator here, Apple Silicon system image)
   - For the desktop client: KDE Craft is bootstrapped by the job itself
     into the runner's home; allow ~20 GB
4. Energy: System Settings -> Battery/Energy -> "Prevent automatic sleeping
   when the display is off" (on power), and keep the lid open or the Mac
   docked while a tag pipeline runs; a `caffeinate -i` wrapper in the
   job script keeps the build awake for its own duration.
5. Verify: push a tag on `drive/ios` (or run the `macos:smoke` job
   manually) and watch the job pick up on this runner.

## Hygiene while the personal Mac is the runner

- Keep `gitlab-runner` current (`brew upgrade gitlab-runner`); the runner
  version must not lag gitlab.com by more than one minor.
- `~/builds` (the runner's working directory) is disposable; clear it if
  disk gets tight, never keep anything there.
- Never store `MATCH_PASSWORD`, API keys or keystores on the machine
  outside the CI job's lifetime; they live in GitLab protected variables.
- When the Mac mini arrives: register it the same way, then
  `gitlab-runner unregister` on the personal Mac and delete the runner in
  GitLab. Nothing in the repos changes.
