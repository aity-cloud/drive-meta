# Tier 1: the Drive server contract test

`drive_contract.py` walks the exact request sequence an Aity Drive Client
makes, against a real Environment, and fails on the first thing a client
could not live with.

## Why it exists

On 2026-08-27 the iOS client logged in and then showed an account that
never loaded. The cause was server-side and invisible to the app: oCIS 8
stamps a last-sign-in time onto the user's LDAP entry, our schema had no
such attribute, so `/graph/v1.0/me` answered 500 on alternate requests.
Production had been doing it about 17 times a day since the oCIS 8 upgrade
and nobody knew. This test turns that class of failure into a red
pipeline.

It complements, and does not replace, the UI tests (Tier 2). This one
answers "is the server still giving clients what they need"; those answer
"does the app do the right thing with it".

## What it checks

1. `/.well-known/webfinger` and `/status.php` - account bootstrap.
2. An OIDC **password grant** against the realm, using the same public
   `drive` client the web UI uses.
3. `/ocs/v2.php/cloud/capabilities` - what the client enables.
4. `/graph/v1.0/me` - the account itself (the one that broke).
5. `/graph/v1.0/me/drives` - and that a **personal** space exists. Without
   it a client has nothing to open, which looks exactly like "the account
   does not load".
6. That the personal space advertises a **WebDAV URL on the same host**. A
   client follows whatever the server advertises; if that is wrong the app
   goes quiet with no error.
7. A real round trip in the user's own space: `PROPFIND`, `PUT`, `GET`
   (retrying while oCIS answers `425 Too Early` during post-processing -
   normal behaviour, every client retries), then `DELETE`, so the run
   leaves nothing behind.

## Its companion: `drive_client_auth.py` (Tier 1.5)

The test above authenticates with a **password grant on the `drive` client**,
because that is the only client the realm allows it on. So it proves nothing
about `drive-android`, `drive-ios` and `drive-desktop` - the three public
clients the apps themselves use, and the ones a broken tofu apply would take
out.

`drive_client_auth.py` walks the real thing for each of them: authorization
request with PKCE S256, the realm's login pages, the redirect back to that
Client's own redirect URI, the token exchange, one refresh, and finally
`/graph/v1.0/me/drives` to check oCIS accepts the token. It runs on the Linux
runner in seconds and is the pre-flight for the expensive Mac jobs in
`drive/ios` and `drive/android` - much better than finding a broken client
registration half an hour into a job on Raul's laptop.

Two things it established on the day it was written (2026-08-27):

- **Refresh tokens work** for `drive-ios` and `drive-android`, with rotation.
  The spec listed this as unverified ("the stock clients are registered with
  `use_refresh_tokens = false`, which is almost certainly wrong for mobile
  apps"), so it is now asserted rather than assumed.
- **`drive-desktop` cannot sign in against staging at all.** The edge answers
  403 (`Server: istio-envoy`, empty body) to any authorization request whose
  `redirect_uri` is loopback, which is the only kind the desktop client has;
  the same request with a non-loopback redirect reaches Keycloak and gets a
  400. It is reported as KNOWN-BLOCKED rather than failing the job, because
  it is a tracked gateway defect - `drive/desktop/MAINTAINING.md`, "Sync
  smoke gap". Remove it from `KNOWN_BLOCKED` the day the WAF rule is fixed.

Two traps it encodes, shared with both UI test suites:

- The realm's browser flow is **identity-first**: page 1 (`login-username`)
  takes the email, page 2 (`login`) takes the password. Posting both at once
  silently redisplays page 1 with no error message.
- The login page is a **React app** (the Keycloakify `aity` theme), so there
  is no server-rendered `<form>`; the POST target is
  `kcContext.url.loginAction`, embedded in the bootstrap script.

## Running it

```sh
export AITY_CONTRACT_USER=drive-contract@aity.works
export AITY_CONTRACT_PASSWORD=...        # protected CI variable
python3 contract/drive_contract.py \
  --base-url https://drive.aity.works \
  --issuer   https://auth.aity.works/realms/aity
```

python3 stdlib only - no dependencies, runs in the plain catalog alpine
image.

## In CI

- `contract:staging` and `client-auth:staging` run on every push to `main`,
  on the schedule, and manually from the UI.
- `contract:production` and `client-auth:production` are **manual** and need
  `AITY_CONTRACT_USER_PROD` / `AITY_CONTRACT_PASSWORD_PROD`; they sign in as
  a real user (and the contract test writes a file), so a human decides when.

```sh
python3 contract/drive_client_auth.py \
  --issuer   https://auth.aity.works/realms/aity \
  --base-url https://drive.aity.works \
  --environment staging
```

## The test account

`drive-contract@aity.works` on the staging realm, created 2026-08-27.
Recreating it (or making the production twin) takes four steps, all
against the admin API with the `tofu-admin` client:

1. `POST /admin/realms/aity/users` with `enabled`, `emailVerified`, and
   **`attributes.phoneNumber`** set. The phone is required for role `user`
   since 2026-08-27; without it the password grant answers
   `Account is not fully set up`.
2. Assign the `ocisUser` role **on the `drive` client** (not a realm role).
3. `PUT /admin/realms/aity/users/<id>` with `{"requiredActions":[]}` -
   new users get `TERMS_AND_CONDITIONS`, which also blocks the grant.
4. Store the credentials as protected CI variables on the
   `aity-cloud/drive` group; the password is masked and never printed.

Traps worth knowing: a federated (LDAP-backed) user cannot have
`phoneNumber` patched on afterwards - there is no LDAP mapper for it, and
a full-representation `PUT` is rejected for touching the read-only
`createTimestamp`/`modifyTimestamp`. Set it at creation, or create a new
account.
