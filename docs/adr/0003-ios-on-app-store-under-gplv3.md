---
status: accepted
---

# iOS ships on the App Store under GPLv3 without an upstream exception

`owncloud/ios-app` is GPLv3, and the only exception ownCloud grants covers
Ad Hoc distribution to at most 100 devices; Apple's App Store terms conflict
with GPLv3 and, unlike Nextcloud (`COPYING.iOS`), ownCloud publishes no
covenant. Kiteworks' OSPO announced (2026-05) a relicensing of the ownCloud
repositories towards Apache-2.0, with no timeline. We decided to publish
Aity Drive for iOS on the App Store anyway, exactly as OpenCloud has since
2025: ownCloud's copyright notices intact, the GPL text and a source link in
the app, and the complete corresponding source of every release published
(ADR 0004). The only party with standing to object is the copyright holder,
which is moving to a permissive licence and has tolerated OpenCloud's
identical listing; waiting for a reply to a covenant request, or buying an
Enterprise Subscription for ownBrander, would block the launch on a risk we
judge small.

## Considered options

- **Request a written covenant first and gate the listing on it**: the
  cleanest outcome, but the request may never be answered and Ad Hoc (100
  devices) is not a launch.
- **ownCloud Enterprise Subscription / ownBrander**: the sanctioned
  commercial route, but unknown pricing, a vendor contract, and the iOS
  artifact would come from their service instead of our GitLab.

## Consequences

- A rights-holder complaint can pull the listing; source availability is
  therefore a hard requirement of every release, never optional.
- Android (GPLv2) and desktop (GPL-2.0-or-later) carry no store conflict;
  this ADR is about iOS only.
- Revisit when `owncloud/ios-app` is relicensed: the conflict then
  disappears and this ADR becomes moot.
