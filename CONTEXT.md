# Aity Drive Clients

The family of end-user apps for the Drive Capability of Aity Business Mail:
the store-published mobile apps and the desktop sync client, produced from
the upstream ownCloud clients, plus the shared vocabulary, decisions and brand
master they derive from. The Drive Capability itself (oCIS, its theme, the
office suite) is defined in `infra/harvester-cluster/CONTEXT.md`; this
context is only about the apps customers install.

## Language

**Aity Drive**:
The customer-facing name of the Drive Capability as seen through any of its
Clients; the web UI already carries it, the installed apps adopt it.
_Avoid_: ownCloud (upstream's name and trademark, never user-facing), Drive
app (ambiguous between Clients)

**Client**:
One of the end-user apps of Aity Drive: Android, iOS, Desktop (Windows,
macOS, Linux) and Web. Web is themed in place on oCIS; the other three are
each produced by a Factory.
_Avoid_: app (store vocabulary, and collides with the oCIS "apps"), frontend

**Stock Client**:
An unmodified Upstream app as ownCloud publishes it, usable against Drive
only because its upstream OIDC client IDs are registered in Keycloak. A
transition-era convenience, retired once the branded Client is in the
stores.
_Avoid_: official app (ours is the official one), vanilla

**Upstream**:
The ownCloud project's own codebase for a Client, which a Factory builds
from: `owncloud/android`, `owncloud/ios-app`, `owncloud/client`.
_Avoid_: origin (a git remote), source (ambiguous with our own)

**Pin**:
The exact Upstream release tag a Factory builds from. The only thing that
moves on a Bump.
_Avoid_: version (that is the Client's own version), base, ref

**Overlay**:
Everything Aity owns on top of the Pin: the Branding, the Patches and the
build recipe. It is the entire content of a Factory's repository.
_Avoid_: fork (implies a copied tree), customisation, skin

**Branding**:
The Upstream-sanctioned configuration and assets (name, icon, colours,
preset server, OIDC client, redirect scheme, help links) that turn a Pin
into Aity Drive without touching source.
_Avoid_: theme (reserved for the Web Client's oCIS theme), white-label (the
policy, not the artifact)

**Patch**:
A source change applied on top of the Pin because Branding cannot express
it. Every Patch is re-validated on every Bump; zero Patches is the target.
_Avoid_: fix, tweak, hack

**Factory**:
The repository that produces one Client's release artifacts from its Pin
plus its Overlay, through CI only. Stores, download pages and infra repos
are consumers and never build. Same meaning as the estate-wide "Factory
Repo" in `infra/harvester-cluster/CONTEXT.md`.
_Avoid_: fork repo, mirror

**Environment build**:
A Client build bound to exactly one Environment (production `aity.tech` or
staging `aity.works`: its server and its Keycloak), carrying its own install
identity so both can live on one device. Every release produces both.
_Avoid_: flavor (Android's word only), scheme, variant, build type

**Public Mirror**:
The public GitHub copy of a Factory, together with the release assets CI
publishes there (installers, update feeds, the materialised source of each
release). A consumer only: never pushed to by hand, never built from.
_Avoid_: the GitHub repo (ambiguous with upstream), fork

**Promote**:
The single manual act that moves a release from the staging tracks to the
public listings and the Public Mirror release. Nothing reaches a customer
without it.
_Avoid_: deploy, publish (CI publishes to staging tracks without a human)

**Bump**:
Moving a Factory's Pin to a newer Upstream release and re-validating the
Overlay against it.
_Avoid_: upgrade (what customers receive), rebase (only a true fork rebases)
