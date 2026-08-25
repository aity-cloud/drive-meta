---
status: accepted
---

# Aity Drive clients are overlay factories, not forks

ABM customers need Aity-branded, preconfigured Drive apps in the stores, and
upstream ownCloud ships an official branding mechanism for every client
(Android `setup.xml`, iOS `Branding.plist` + assets, desktop OEM theme). We
decided that each client is an overlay factory: the repository holds only
what we own - the Pin, the Branding, the Patches and the CI recipe - and CI
materialises upstream at the Pin, lays the Overlay on top, applies Patches
and builds. v1 is white-label only: no Aity-specific features, zero Patches
as the target. The diff we own stays small and readable, a Bump is a
one-line Pin change plus re-validation, and licence exposure is limited to
what Branding cannot express. This is the same shape as the estate's other
factory repos (`custom-oss/ocis`, `custom-oss/twenty-crm`).

## Considered options

- **True fork branch** (full upstream tree, an `aity` branch rebased or
  merged on every release): opens directly in Android Studio/Xcode, but our
  changes drown in a 100k-file tree, every Bump is a merge, and it invites
  drift into feature work.
- **ownCloud's commercial branded-client programme**: nothing to maintain,
  but not built by our GitLab, and it ties the product to ownCloud/Kiteworks
  commercial terms.

## Consequences

- Local development needs a materialise step (clone Pin, apply Overlay)
  before the project opens in an IDE; the Factory provides it as a script.
- Anything Branding cannot express becomes a Patch, i.e. a liability on
  every Bump - the bar for accepting one is "the app is not shippable
  without it".
