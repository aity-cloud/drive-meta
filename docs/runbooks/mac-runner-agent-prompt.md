# Agent prompt: bring up the `macos` GitLab runner

Paste everything below the line into Claude Code (or any capable agent)
**running on the Mac**. It is self-contained: the agent discovers what it
needs, asks the human only for the two things a human must do, and proves
the result with a real pipeline job.

Human prerequisites: the Mac is signed in as the user who will own the
runner, has `gh`/`glab` or the ability to install them, and can reach
gitlab.com. Nothing else.

Companion doc for the reasoning behind the design: `mac-runner.md`.

---

You are setting up this Mac as a self-managed GitLab runner for the Aity
Drive client factories. Work autonomously; ask the human only where this
prompt says to. Report what you did at the end.

## Context you need

- The runner serves the GitLab subgroup `aity-cloud/drive` (group id
  **140496714**) on gitlab.com. Its repos: `meta`, `android`, `ios`,
  `desktop`, `certificates`.
- The runner must be tagged **`macos`**, must NOT run untagged jobs, and
  must be **protected** (protected branches/tags only).
- It runs as a **shell executor under the logged-in user session** (a
  LaunchAgent, never a LaunchDaemon): codesign, the keychain and the iOS
  simulator do not work from a daemon context.
- Jobs it will run: iOS simulator builds + XCUITest smoke (`drive/ios`),
  the macOS desktop client build (`drive/desktop`), and the Android
  emulator smoke (`drive/android`). All are currently `when: manual`.
- This Mac is transitional; a dedicated Mac mini replaces it later. Change
  nothing in the repos to accommodate this machine.

## Step 1 - tools

Install what is missing (Homebrew is expected; install it if absent):

```sh
brew install gitlab-runner xcodes glab
brew install --cask android-commandlinetools   # for the Android emulator smoke
```

Xcode: read the Pin's required version from the factory rather than
guessing -

```sh
glab api projects/aity-cloud%2Fdrive%2Fios/repository/files/.xcode-version/raw?ref=main
```

(if that path 404s, look for `.xcode-version` in the materialized upstream
tree referenced by `drive/ios/UPSTREAM.md`; at the time of writing it is
**26.2**). Then:

```sh
xcodes install <version> --select
sudo xcodebuild -license accept
xcodebuild -runFirstLaunch
```

Ensure an iOS simulator runtime matching that Xcode is installed
(`xcodebuild -downloadPlatform iOS` or via Xcode > Settings > Components).

Android SDK bits for the emulator smoke:

```sh
sdkmanager "platform-tools" "emulator" "system-images;android-35;google_apis;arm64-v8a"
```

Export `ANDROID_HOME` (and `$ANDROID_HOME/platform-tools` on PATH) in the
runner user's shell profile - the runner inherits the login shell
environment.

## Step 2 - create the runner in GitLab

Preferred, no browser needed (GitLab 16+ API). Requires `glab` authenticated
as a user with Maintainer/Owner on the group:

```sh
glab auth status   # authenticate first if needed: glab auth login
glab api -X POST user/runners \
  -f runner_type=group_type \
  -f group_id=140496714 \
  -f "description=$(scutil --get ComputerName) (transitional)" \
  -f "tag_list=macos" \
  -F run_untagged=false \
  -F access_level=ref_protected \
  -F locked=true
```

The response contains a `token` starting `glrt-`. **It is shown once.** Keep
it only in memory for the next step; never write it to a file in a repo,
never echo it into a transcript you will paste somewhere.

If the API call is refused (permissions or GitLab version), ask the human to
create it in the UI instead: GitLab -> group `aity-cloud/drive` -> Build ->
Runners -> New group runner, tags `macos`, untick "Run untagged jobs", tick
"Protected", then hand you the `glrt-...` token.

## Step 3 - register and start

```sh
gitlab-runner register --non-interactive \
  --url https://gitlab.com \
  --token "$RUNNER_TOKEN" \
  --executor shell \
  --shell bash \
  --description "$(scutil --get ComputerName) (transitional)"

gitlab-runner install    # as the LOGIN user, no sudo - this is the LaunchAgent
gitlab-runner start
gitlab-runner verify
```

If `gitlab-runner install` was ever run with `sudo` on this machine, undo it
(`sudo gitlab-runner uninstall`) before installing as the user: a
LaunchDaemon has no GUI session and every codesign/simulator job will fail
in confusing ways.

Concurrency: set `concurrent = 1` in `~/.gitlab-runner/config.toml` (these
are heavy builds and this is somebody's laptop), then
`gitlab-runner restart`.

## Step 4 - energy and disk

- System Settings -> Battery/Lock Screen: prevent automatic sleeping while
  on power. A sleeping Mac just stalls pipelines, it breaks nothing.
- Keep at least ~40 GB free: Xcode, a simulator runtime, KDE Craft's build
  tree for the desktop client and the runner's `~/builds` add up.

## Step 5 - prove it, with a real job

Do not declare success on `gitlab-runner verify` alone. Trigger the cheapest
real job and watch it run on THIS runner:

```sh
# iOS: the simulator smoke needs no Apple account and no signing
glab ci run -R aity-cloud/drive/ios -b main
# then play the manual job named `smoke:simulator` (or `build:simulator`)
glab ci list -R aity-cloud/drive/ios
```

Alternatively `drive/desktop`'s `build:macos` job (heavier, ~20-40 min, and
it will be unsigned until Developer ID certificates exist - that is
expected).

Report for each attempted job: did it pick up on this runner, did it pass,
and if it failed, the exact error. Failures here are EXPECTED to be
informative: the iOS factory has never been built on a Mac (everything
Xcode-side is marked UNVERIFIED in `drive/ios/MAINTAINING.md`), so the first
run is also the first real test of that factory. Capture the errors
faithfully - they are the point of this exercise, not a reason to improvise
fixes in the repos.

## Boundaries

- Do NOT commit anything to any Aity repo from this Mac. If a factory needs
  a fix, report the diagnosis; the fix lands from the main workstation.
- Do NOT put signing material, App Store Connect keys or `MATCH_PASSWORD`
  on this machine outside a CI job's lifetime. They live in GitLab
  protected variables.
- Do NOT disable Gatekeeper, SIP, or the firewall, and do not add sudoers
  entries for the runner.
- If asked for a GitLab token beyond the runner token above, stop and ask
  the human.

## Done means

1. `gitlab-runner verify` lists the runner as alive.
2. The runner appears in GitLab under the `aity-cloud/drive` group, tagged
   `macos`, protected, not accepting untagged jobs.
3. At least one real job from `drive/ios` or `drive/desktop` was picked up
   by it, with its outcome reported.
