# Runbook: publisher accounts and code signing (M0)

Everything a human (Raul, as owner of AITY CLOUD SRL) has to obtain before
a Client can be signed or listed. Facts checked against the vendors' own
pages on 2026-08-25; items marked "unverified" could not be confirmed from
a primary source. Order = critical path: start step 1 today, the rest are
days.

## 0. One identity, spelled identically everywhere

Every vendor cross-checks the legal entity against Dun & Bradstreet, and
Google restricts the account when its payments profile differs from the
D&B record. Before touching any form, fix the canonical strings and use
them verbatim (ONRC spelling of the name, including whether it is "S.R.L."
or "SRL"):

| Field | Value |
|---|---|
| Legal name | AITY CLOUD SRL (confirm the exact ONRC form) |
| CUI | 39458128 |
| Registered office | SĂCEL nr. 1003, Sat Săcel, Com. Săcel, MARAMUREȘ, 437290, Romania (as in the onboarding contract) |
| Phone | +40735850896 |
| Work email on a company domain | office@aity.ro (Apple and Google both require a company-domain address; Google says the org contact email must not be generic or personal, i.e. not gmail) |
| Public website | https://aity.ro (Apple requires a publicly functional site on a company domain - `https://aity.tech/` currently answers 404, so use aity.ro or fix the root first) |
| Apple Account for the Account Holder | Raul's, 2FA on, legal first/last name |

Lead times, longest first:

| Step | Published lead time |
|---|---|
| D-U-N-S | D&B: "in most cases within 30 business days"; via Apple's request tool up to 5 business days at D&B + 2 to propagate to Apple; Google: "can take up to 30 days" |
| Azure Artifact Signing identity validation | 1 to 20 business days |
| Apple organisation enrolment | no SLA; support verifies, then emails next steps; confirmation within 24 h of paying |
| Google Play organisation verification | "a few days" after documents |
| Google Play target API | new apps must target API 36 from **2026-08-31** (extension to 2026-11-01 requestable) - check the Android Pin's `targetSdk` before the first upload |

## 1. D-U-N-S number

1. Sign in with the Apple Account first (the lookup tool redirects to
   idmsa), then use https://developer.apple.com/enroll/duns-lookup/ with
   the legal entity name, HQ address, mailing address and a work contact.
   If nothing is found the tool files a FREE request with D&B on your
   behalf. Reference: https://developer.apple.com/support/D-U-N-S/
2. Romania is served by D&B's Worldwide Network partner ICAP CRIF
   (Global City Business Park, Voluntari, +40 21 206 24 60,
   customercare@icapcrif.com, https://icapcrif.com/en/duns-number/).
   Whether ICAP CRIF charges for local issuance is unverified; the Apple
   path is free.
3. Pitfall: "Your organization is not listed as a legal entity" = D&B has
   the wrong legal status; send registration documents through
   https://support.dnb.com/?CUST=APPLEDEV. Expediting D&B does not shorten
   the 2-business-day propagation to Apple; edits to the profile take the
   same 2 days.
4. Keep the number: Apple, Google and Azure all ask for it.

## 2. Apple Developer Program (organisation)

Reference: https://developer.apple.com/support/enrollment/ and
https://developer.apple.com/help/account/membership/program-enrollment/

1. Enrol on the WEB (organisations cannot use the Apple Developer app):
   https://developer.apple.com/programs/enroll/ as the owner/founder, so
   no third-party authority reference is needed. Have: D-U-N-S, legal
   entity name, work email, website, phone; Apple may ask for photo ID and,
   region-dependent, notarised registration documents.
2. Apple Developer Support verifies and emails; the Account Holder accepts
   the Program License Agreement and pays 99 USD/year (local currency and
   VAT at checkout; the EUR/RON figure is unverified). Free apps need no
   Paid Apps Agreement.
3. EU obligations right after enrolment (both block submissions if missing):
   - Digital Services Act trader status: App Store Connect > Business >
     Agreements > Compliance > Digital Services Act. Address is taken from
     the D-U-N-S record; phone and email are code-verified and PUBLISHED
     on the product page in all EU storefronts.
     https://developer.apple.com/help/app-store-connect/manage-compliance-information/manage-european-union-digital-services-act-trader-requirements
   - Invoicing requirements: update the account within 15 days of Apple's
     notice so the fee is invoiced B2B.
     https://developer.apple.com/help/app-store-connect/distributing-apps-in-the-european-union/update-your-account-for-invoicing-requirements/
4. CI access - App Store Connect > Users and Access > Integrations >
   Team key: role App Manager, download the `.p8` ONCE, note Key ID and
   Issuer ID; store as protected CI variables `ASC_KEY_ID`, `ASC_ISSUER_ID`,
   `ASC_KEY_P8` (file). The same key drives `pilot`/`deliver` and
   `notarytool` (`--issuer` is required for Team keys).
   https://developer.apple.com/help/app-store-connect/get-started/app-store-connect-api/
5. Identifiers (Certificates, Identifiers & Profiles), per the identity
   table in `specs/aity-drive-v1.md`, for BOTH Environment builds:
   explicit App IDs `tech.aity.drive`, `.fileprovider`, `.fileprovider-ui`,
   `.intents`, `.share`, `.action` and their `.staging` twins; App Groups
   `group.tech.aity.drive` / `group.tech.aity.drive.staging` for iOS.
   macOS caveat: on macOS 15+ an app group must be Team-ID-prefixed
   (`<TEAMID>.tech.aity.drive`) or authorised by an embedded Developer ID
   provisioning profile - the desktop Factory uses the Team-ID form and a
   Developer ID profile (18-year validity; an expired profile stops the app
   from launching).
   https://developer.apple.com/help/account/identifiers/register-an-app-id/
   https://developer.apple.com/help/account/reference/supported-capabilities-macos/
6. Certificates: ONE Apple Distribution certificate per team (match
   creates it); Developer ID Application + Installer certificates are
   created by the ACCOUNT HOLDER only, maximum 5 of each, valid 5 years.
   Then bootstrap the match store: `bundle exec fastlane match appstore`
   and `match developer_id` from a Mac with the passphrase; the passphrase
   becomes the protected variable `MATCH_PASSWORD`.
   https://developer.apple.com/help/account/certificates/create-developer-id-certificates/
7. Notarisation from CI: `xcrun notarytool submit --issuer --key-id --key
   --wait`, then `xcrun stapler staple` on each item (never a zip);
   `notarytool log <id>` on failure. Minimum role for the key: "Developer"
   per third-party docs, unverified from Apple.
   https://developer.apple.com/documentation/security/customizing-the-notarization-workflow

Per-app metadata the reviewer will check (App Store Connect):
- Guideline 2.1: "Sign-in required" with the `appreview@` credentials
  (decision 17); the demo account must not expire; notes up to 4000 bytes.
- 5.1.1: privacy policy URL `https://aity.tech/documents/privacy/` in the
  metadata AND in the app; App Privacy labels are mandatory (we declare no
  third-party SDKs; ownCloud's own data flows only).
- Age rating questionnaire (new 2026 questions apply to every new app).
- Export compliance: `ITSAppUsesNonExemptEncryption = NO` (OS-provided TLS
  only) skips the per-build question.
- Business model: a client for a service bought elsewhere is allowed
  (3.1.3(b) multiplatform services, 3.1.3(e)); nothing is sold in-app, so
  no IAP; 4.2 wants more than a repackaged website - a native sync client
  clears that.
  https://developer.apple.com/app-store/review/guidelines/

## 3. Google Play Console (organisation)

### State 2026-09-02: the org account EXISTS - Raul's remaining checklist

The account-creation steps below are DONE. Machine-side preparation is also
done: the upload keystore is generated (PKCS12, alias `upload`, RSA 4096,
~30y) and lives ENCRYPTED in `drive/certificates/android/` (passphrase:
`MATCH_PASSWORD`); `v*` tags on drive/android are protected (they were not,
and protected variables never reach unprotected refs - check that first on
every new Factory); the android build decodes the keystore variable from
base64 (CI variables are text, a raw binary JKS gets mangled).

DONE 2026-09-02 (with Raul's explicit authorization in chat): the
encrypted keystore + `set-ci-variables.sh` are pushed in
`drive/certificates/android/`, and the four `ANDROID_UPLOAD_KEYSTORE*`
protected variables are set on drive/android. The script re-creates the
variables from the repo alone (export `MATCH_PASSWORD`, run it) if they
are ever lost.

### The service account, as actually clicked (2026-09-02) - the record

Done in the EXISTING GCP project **`aity-tech`** (the one that also holds
the reCAPTCHA), NOT a dedicated project - one less project to keep alive
for decades, and the SA's power comes from the Play Console invite, not
from GCP roles anyway. The exact clicks, for the next app and the next
decade:

1. console.cloud.google.com, project `aity-tech` > search "Google Play
   Android Developer API" > Enable.
2. IAM & Admin > Service Accounts > Create service account, name
   `play-publisher`, NO GCP roles (skip both optional steps). Result:
   `play-publisher@aity-tech.iam.gserviceaccount.com`.
3. The SA > Keys > Add key > Create new key > JSON > download once.
4. play.google.com/console > Users and permissions > Invite new users >
   the SA email > ACCOUNT permissions: "Release apps to testing tracks",
   "Release to production, exclude devices, and use Play App Signing",
   "Manage testing tracks and edit tester lists", "Manage store
   presence" > Invite. Account-level so every future app (Aity Business
   Mail, ...) inherits it with zero extra clicks.
5. The JSON key now lives as `PLAY_SERVICE_ACCOUNT_JSON` (protected,
   file type) on drive/android, with an encrypted backup at
   `drive/certificates/android/play-service-account.json.enc`
   (passphrase `MATCH_PASSWORD`); the plaintext download was deleted.
   A future factory just gets its own copy of the variable - same SA.

**Verifying it**: `drive/certificates/android/check-play-access.sh`
(export `MATCH_PASSWORD`, run it) mints a token and proves the chain
per app without spending a pipeline. Token minting worked immediately;
the androidpublisher calls answered 403 on day one - that is the invite
propagation (up to ~24h) if step 4 is done, or step 4 missing. Rerun
until both apps report OK (a 404 just means the app entry has no build
yet - expected before the first upload).

What remains is Raul's, in order:

5. In the Play Console UI, create BOTH app entries (Home > Create app):
   name "Aity Drive" / "Aity Drive (staging)", English (US), App, Free,
   tick the declarations. The API cannot create apps; the package names
   (`tech.aity.drive` / `.staging`) bind at the first upload, nothing to
   type here.
6. Cut the release tag (`v4.8.3-aity-1`) on drive/android, run the
   `smoke:emulator` job and the real-device pass
   (`drive/android/MAINTAINING.md`, "Real-device pass"), then trigger
   `publish-staging` (staging app -> internal track) and `promote`
   (production app -> production, draft). First-upload caveat: fastlane
   documents that a brand-new app's first build must be uploaded by hand
   in the Console; the deploy lane's `release_status: draft` is reported
   to work anyway. Try the job first; if the API refuses with app/package
   not found, upload the CI-BUILT AAB from the pipeline artifacts once
   through the Console UI (still CI's artifact - the no-manual-BUILD rule
   holds) and use the jobs from then on.
7. Before the production listing can go PUBLIC (internal track needs
   none of this): 2+ phone screenshots (`fastlane/metadata` holds only
   `.gitkeep`s), 1024x500 feature graphic, IARC content rating, data
   safety form. Listing texts (en-US, ro) and the privacy policy URL
   already exist.

References: https://support.google.com/googleplay/android-developer/answer/13628312 ,
https://support.google.com/googleplay/android-developer/answer/10840893 ,
https://support.google.com/googleplay/android-developer/answer/14177239

1. Create the account as an ORGANISATION with the D-U-N-S; fields: public
   developer name (AITY CLOUD SRL), org address, phone, website (not shown),
   contact name/email/phone (OTP-verified, company-domain email), and the
   developer email + phone that are DISPLAYED on Google Play (choose an
   address you are happy to publish).
2. Pay the one-time 25 USD by card through Google Pay (email receipt only;
   Google issues no invoice - VAT treatment unverified).
3. Verification: owner's government photo ID + proof of business
   registration matching the D&B profile; a Google payments profile whose
   owner is an account admin; "a few days".
4. The 12-testers/14-days closed-test rule is scoped to PERSONAL accounts
   created after 2023-11-13; an organisation account is not subject to it.
   https://support.google.com/googleplay/android-developer/answer/14151465
5. Per app, before the first production release:
   - Play App Signing (automatic for new apps): we keep an RSA-2048 upload
     keystore as a protected file variable; Google holds the app key; a
     lost upload key is resettable.
   - Data safety form (mandatory even with no data collection) + privacy
     policy URL on the listing and in the app; IARC content rating.
   - target API 36 from 2026-08-31 (see lead-time table).
6. CI service account: no Cloud-project linking needed any more - create a
   GCP project, enable "Google Play Android Developer API", create a service
   account + JSON key (protected file variable `PLAY_SERVICE_ACCOUNT_JSON`),
   then Play Console > Users & permissions > Invite new users with the
   service-account email and grant: "Release to production, exclude
   devices, and use Play App Signing", "Release apps to testing tracks",
   "Manage testing tracks and edit tester lists", "Manage store presence".
   https://developers.google.com/android-publisher/getting_started
   Two known traps: the FIRST build of a new app must be uploaded by hand
   in the console (fastlane `supply` and Gradle Play Publisher both say so),
   and third-party docs report up to 24 h before a new service account is
   honoured (folklore, not in Google's docs).
7. DSA trader declaration: Google shows the verified developer name,
   email and phone on Play; a dedicated Play Console DSA article could not
   be located (unverified) - check the account's business information page.

## 4. Windows code signing

Chosen: **Azure Artifact Signing** (the renamed Azure Trusted Signing;
same service). https://azure.microsoft.com/en-us/products/artifact-signing

1. Eligibility: Public Trust certificates for organisations in the EU,
   among others - Romania qualifies. Community answers cite a "verifiable
   tax history of three or more years" for organisations (not on the
   Learn pages - unverified); AITY CLOUD SRL's 2018-era CUI should clear it.
2. Cost: Basic 9.99 USD/month, 5,000 signatures, 1 certificate profile;
   Premium 99.99 USD/month. Paid subscription only, no free tier.
   https://azure.microsoft.com/en-us/pricing/details/artifact-signing/
3. Create the Artifact Signing account in West Europe
   (`https://weu.codesigning.azure.net`), then Identity validation in the
   portal (role "Artifact Signing Identity Verifier"): org name, website,
   primary + secondary email on the company domain (link expires in 7
   days), business identifier, address, and one person who completes
   individual verification via AU10TIX + Microsoft Authenticator Verified
   ID; documents issued within 12 months; 3 upload attempts; 1-20 business
   days. https://learn.microsoft.com/en-us/azure/artifact-signing/quickstart
4. Certificate profile: Public Trust; no EV, no custom CN/O; keys are
   HSM-held with 3-day certificate validity, so timestamping
   (`http://timestamp.acs.microsoft.com`) is mandatory in every signature.
5. CI: a service principal with the "Artifact Signing Certificate Profile
   Signer" role; secrets `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`,
   `AZURE_CLIENT_SECRET` as protected variables. Two ways to sign:
   - on the hosted Windows runner: SignTool + `Azure.CodeSigning.Dlib.dll`
     (NuGet `Microsoft.ArtifactSigning.Client`) + `metadata.json`;
   - on the LINUX runner: Jsign with `--storetype TRUSTEDSIGNING`
     (keystore = endpoint, alias = `<account>/<profile>`, storepass = an
     `az account get-access-token --resource https://codesigning.azure.net`
     token). This lets the Windows job stop at "unsigned installer
     artifact" and the cheap Linux job sign it - fewer purchased minutes.
     https://ebourg.github.io/jsign/
6. SmartScreen: Microsoft states EV certificates no longer bypass
   SmartScreen; every certificate type starts with a warning and builds
   reputation over time; only Store distribution is warning-free. Expect
   warnings on the first weeks of downloads regardless of vendor.
   https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation

Fallbacks if Azure's identity validation fails: an OV certificate from a
public CA on a cloud HSM (SSL.com eSigner from ~20 USD/month, Certum
SimplySign OV from EUR 209, DigiCert KeyLocker), all usable from CI via
Jsign; or SignPath Foundation's free open-source signing (a GPL desktop
client maintained in a public repo may qualify; requires manual approval
of every release and an attribution line on the project page,
https://signpath.org/terms).

## 5. Where the secrets go

All protected + masked-where-possible, tag-protected refs only, on the
factory projects (never the mirrors, never the meta repo):

| Variable | Repo | Source |
|---|---|---|
| `ASC_KEY_ID`, `ASC_ISSUER_ID`, `ASC_KEY_P8` (file) | ios, desktop | step 2.4 |
| `MATCH_PASSWORD`, `MATCH_GIT_PRIVATE_KEY` (file; deploy key on `drive/certificates`) | ios, desktop | step 2.6 |
| `ANDROID_UPLOAD_KEYSTORE` (file, BASE64 of the .jks), `ANDROID_UPLOAD_KEYSTORE_PASSWORD`, `ANDROID_UPLOAD_KEY_ALIAS`, `ANDROID_UPLOAD_KEY_PASSWORD` | android | generated 2026-09-02; encrypted backup + `set-ci-variables.sh` in `drive/certificates/android/` (passphrase `MATCH_PASSWORD`) |
| `PLAY_SERVICE_ACCOUNT_JSON` (file) | android | step 3.6 |
| `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` | desktop | step 4.5 |
| `GITHUB_MIRROR_KEY` (file) | all four | `scripts/mint-mirror-keys.sh` (done) |

## 6. Done / not done (keep current)

- [~] D-U-N-S: requested 2026-08-25. NOTE: Raul already holds an
      **individual** Apple Developer account; Apple is converting it to an
      **organization** once the D-U-N-S lands. That conversion, not a fresh
      enrolment, is the path here - the org entity name becomes the App
      Store seller name, and only after it completes do the organization-only
      artefacts exist (Developer ID certificates for macOS, Team API keys
      with org roles, the DSA trader form)
- [ ] Apple account CONVERTED to organisation (in progress); DSA trader + EU invoicing set
- [ ] App Store Connect Team API key in CI variables
- [ ] Identifiers + app groups registered; match store bootstrapped
- [x] Google Play organisation verified (2026-09-02)
- [x] Android upload keystore generated + encrypted in drive/certificates; v* tags protected on drive/android (2026-09-02)
- [ ] Play service account created + invited; `PLAY_SERVICE_ACCOUNT_JSON` and `ANDROID_UPLOAD_KEYSTORE*` variables set; both app entries created (the section-3 checklist)
- [ ] Azure Artifact Signing identity validated; certificate profile + service principal
- [x] GitHub mirrors wired with per-repo deploy keys (2026-08-25)
