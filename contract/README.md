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

- `contract:staging` runs on every push to `main`, on the schedule, and
  manually from the UI.
- `contract:production` is **manual** and needs `AITY_CONTRACT_USER_PROD` /
  `AITY_CONTRACT_PASSWORD_PROD`; it signs in as a real user and writes a
  file, so a human decides when.

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
