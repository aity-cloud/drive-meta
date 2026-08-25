---
status: accepted
---

# The Drive clients live in `aity-cloud/drive/` with a `meta` repo

Three factories with three upstream cadences share one glossary, one set of
decisions and one brand master. We decided on a dedicated subgroup
`aity-cloud/drive/` holding `meta` (this repo: CONTEXT.md, ADRs, specs,
brand master) beside `android`, `ios` and `desktop`, one Factory each -
the `crate/` pattern. One repo per upstream keeps the factory tag contract
(`v<upstream>-aity-<n>` per repo) exact and each pipeline's runner needs
separate; the subgroup gives shared docs a home that `custom-oss/` (factories
filed by upstream name, no product grouping) lacks; and, per the crate rule,
the upstream trademark stays out of our group and repo names.

## Considered options

- **Three repos under `custom-oss/`** (`owncloud-{android,ios,desktop}`):
  matches where `ocis` lives, but no home for shared docs and "owncloud" in
  our repo names.
- **One monorepo**: one place for everything, but three Pins and three
  release cadences in one repo force client-prefixed tags and
  `rules: changes:` plumbing in a single large CI file.

## Consequences

- Per-platform Branding assets (adaptive icon layers, asset catalogues,
  ICO/ICNS) are derived in each Factory from the master in `meta`; the
  master is the only place the logo and palette are edited.
- `custom-oss/` remains the home for factories that have no product
  subgroup of their own; it is not "every factory".
