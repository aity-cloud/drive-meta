// Renovate CE configuration for the drive subgroup (run by the `renovate`
// job in .gitlab-ci.yml on a weekly schedule). Central config on purpose:
// the Factories stay minimal Overlays (ADR 0001), so no renovate.json lands
// in them (requireConfig optional + onboarding off).
module.exports = {
  platform: 'gitlab',
  endpoint: 'https://gitlab.com/api/v4',
  autodiscover: true,
  autodiscoverFilter: ['aity-cloud/drive/*'],
  onboarding: false,
  requireConfig: 'optional',
  // Commit identity rule for the subgroup (meta/AGENTS.md).
  gitAuthor: 'Renovate Bot <raul@aity.ro>',
  branchPrefix: 'renovate/',
  labels: ['renovate'],
  prHourlyLimit: 0,
  prConcurrentLimit: 10,
  // A Factory is an Overlay, never the upstream tree (ADR 0001), so the
  // dependency surface is deliberately tiny: CI job images (gitlabci), the
  // fastlane Gemfiles the android/ios Factories carry (bundler - how the
  // "fastlane" toolchain bumps promised in docs/maintenance.md arrive),
  // and the annotated upstream Pins (custom.regex below). gradle and
  // cocoapods stay OFF: the build trees those managers parse belong to the
  // Upstream and reach us only through a Bump - the one gradle change we
  // carry is a Patch file, which no manager reads.
  enabledManagers: ['gitlabci', 'bundler', 'custom.regex'],
  customManagers: [
    // Any CI variable annotated with a renovate comment on the line above,
    // the exact crate/directpv shape (docs/maintenance.md "Upstream watch"):
    //   # renovate: datasource=github-tags depName=owncloud/android
    //   UPSTREAM_TAG: "v4.8.3"
    // An MR on an UPSTREAM_TAG is a SIGNAL that upstream released, NOT a
    // mergeable change. The Bump is a human act (docs/maintenance.md
    // "Per-Bump checklist"): read the upstream release notes, move the Pin,
    // re-validate every Patch, tag v<upstream>-aity-1, verify the staging
    // Environment build, promote.
    {
      customType: 'regex',
      managerFilePatterns: ['/\\.gitlab-ci\\.yml$/'],
      matchStrings: [
        '# renovate: datasource=(?<datasource>\\S+) depName=(?<depName>\\S+)\\n\\s*\\w+: "(?<currentValue>[^"]+)"',
      ],
    },
  ],
};
