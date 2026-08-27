#!/usr/bin/env python3
"""Tier 1.5: can each Client's OIDC registration actually sign a user in?

`drive_contract.py` proves the SERVER still gives clients what they need. It
authenticates with a password grant on the `drive` client, because that is the
only client the realm allows it on - so it says nothing about the three public
clients the apps themselves use (`drive-ios`, `drive-android`,
`drive-desktop`).

This walks the real thing for each of them: authorization request with PKCE
S256, the realm's login pages, the redirect back to the app's own redirect
URI, the token exchange, and one refresh. Then it asks oCIS whether it accepts
the resulting token. It is what the UI tests (Tier 2) need to be true before
they are worth starting, and it runs on the Linux runner in seconds - which
matters, because the alternative is discovering a broken client registration
half an hour into a job on Raul's laptop.

It found two things on the day it was written (2026-08-27):

  - `drive-desktop` cannot be used against staging at all: the edge answers
    403 to any authorization request whose redirect_uri is loopback, which is
    the only kind the desktop client has. `drive/desktop/MAINTAINING.md` has
    the isolation.
  - refresh tokens DO work for the mobile clients, with rotation. The spec
    flagged this as unverified ("the stock clients are registered with
    use_refresh_tokens = false, which is almost certainly wrong for mobile
    apps"), so it is asserted here rather than assumed.

python3 stdlib only, so it runs in the plain catalog alpine image.

Usage:
    drive_client_auth.py --issuer https://auth.aity.works/realms/aity \\
                         --base-url https://drive.aity.works \\
                         --environment staging

Credentials come from the environment (protected CI variables):
    AITY_CONTRACT_USER, AITY_CONTRACT_PASSWORD
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import http.cookiejar
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

TIMEOUT = 30

# The identity table of specs/aity-drive-v1.md, decision 4. Keys are the
# Keycloak clientIds; the redirect is the one the BUILD of that Environment
# carries, so a mismatch here is a mismatch a user would hit.
CLIENTS = {
    "staging": [
        ("drive-android", "aitydrive-staging://android.aity.works"),
        ("drive-ios", "aitydrive-staging://ios.aity.works"),
        ("drive-desktop", "http://127.0.0.1:51234"),
    ],
    "production": [
        ("drive-android", "aitydrive://android.aity.tech"),
        ("drive-ios", "aitydrive://ios.aity.tech"),
        ("drive-desktop", "http://127.0.0.1:51234"),
    ],
}

# The desktop client's loopback redirect is currently blocked by the edge WAF
# (drive/desktop/MAINTAINING.md, "Sync smoke gap"). Until that is fixed the
# job would be permanently red for a known, tracked reason, which trains
# people to ignore it. It is reported loudly and does not fail the run.
# Was {"drive-desktop"}: the staging gateway 403'd every loopback redirect,
# so the desktop client could not sign in at all. Fixed 2026-08-27 by adding
# the 10023/10024 WAF twin to gateway-external-staging and listing the drive
# ids on both gateways (infra/harvester-cluster platform/istio). All three
# clients are expected to pass now - if one blocks again, fix the gateway
# rather than re-adding it here.
KNOWN_BLOCKED: set[str] = set()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(newurl, code, msg, headers, fp)


def pkce_pair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(os.urandom(40)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return verifier, challenge


def page_id(page: str) -> str:
    match = re.search(r'"pageId"\s*:\s*"([^"]*)"', page)
    return match.group(1) if match else "unknown"


def login_action(page: str) -> str | None:
    """The realm runs the Keycloakify `aity` theme: a React app, so there is no
    server-rendered <form> to scrape. The POST target is
    kcContext.url.loginAction, embedded in the bootstrap script."""
    match = re.search(r'"loginAction"\s*:\s*"([^"]+)"', page)
    return html.unescape(match.group(1)).replace("\\/", "/") if match else None


def check_client(issuer: str, base_url: str, client_id: str, redirect_uri: str,
                 username: str, password: str) -> tuple[bool, list[str]]:
    notes: list[str] = []
    verifier, challenge = pkce_pair()
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    noredir = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar), NoRedirect)

    query = urllib.parse.urlencode({
        "client_id": client_id,
        "response_type": "code",
        "scope": "openid profile email offline_access",
        "redirect_uri": redirect_uri,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": "contract",
        "nonce": "contract",
    })
    try:
        page = opener.open(f"{issuer}/protocol/openid-connect/auth?{query}",
                           timeout=TIMEOUT).read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        server = (err.headers or {}).get("Server", "?")
        notes.append(f"authorization request refused: HTTP {err.code} (Server: {server})")
        if err.code == 403 and server.startswith("istio"):
            notes.append("403 from the gateway with no body is the WAF, not Keycloak")
        return False, notes

    def post(url: str, fields: dict) -> tuple[str, str | None]:
        request = urllib.request.Request(
            url, data=urllib.parse.urlencode(fields).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"})
        try:
            response = noredir.open(request, timeout=TIMEOUT)
            return response.read().decode("utf-8", "replace"), None
        except urllib.error.HTTPError as err:
            if 300 <= err.code < 400:
                return "", err.headers.get("Location", "")
            return err.read().decode("utf-8", "replace"), None

    action = login_action(page)
    if action is None:
        notes.append(f"no loginAction on the '{page_id(page)}' page")
        return False, notes

    # The realm's browser flow is IDENTITY-FIRST: username page, then password
    # page. Posting both at once silently redisplays page 1 with no error.
    location = None
    if page_id(page) == "login-username":
        page, location = post(action, {"username": username})
        if location is None:
            action = login_action(page)
            if action is None:
                notes.append(f"no loginAction on the '{page_id(page)}' page after the username step")
                return False, notes
    if location is None:
        body, location = post(action, {"password": password, "credentialId": ""})
        if location is None:
            notes.append(f"login did not redirect; the page is '{page_id(body)}'")
            return False, notes

    if not location.startswith(redirect_uri):
        notes.append(f"redirected to {location[:80]} instead of {redirect_uri}")
        return False, notes
    code = urllib.parse.parse_qs(urllib.parse.urlparse(location).query).get("code", [""])[0]
    if not code:
        notes.append(f"redirect carries no authorization code: {location[:120]}")
        return False, notes
    notes.append(f"login -> {redirect_uri} with a code")

    try:
        tokens = json.loads(urllib.request.urlopen(urllib.request.Request(
            f"{issuer}/protocol/openid-connect/token",
            data=urllib.parse.urlencode({
                "grant_type": "authorization_code", "client_id": client_id,
                "code": code, "redirect_uri": redirect_uri,
                "code_verifier": verifier}).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"}),
            timeout=TIMEOUT).read())
    except urllib.error.HTTPError as err:
        notes.append(f"token exchange failed: HTTP {err.code} {err.read()[:160]!r}")
        return False, notes

    ok = True

    # An app that has to send the user back to a browser every five minutes is
    # not usable. The spec asks for this explicitly.
    if not tokens.get("refresh_token"):
        notes.append("NO refresh_token - the app cannot keep the user signed in")
        ok = False
    else:
        try:
            refreshed = json.loads(urllib.request.urlopen(urllib.request.Request(
                f"{issuer}/protocol/openid-connect/token",
                data=urllib.parse.urlencode({
                    "grant_type": "refresh_token", "client_id": client_id,
                    "refresh_token": tokens["refresh_token"]}).encode(),
                headers={"Content-Type": "application/x-www-form-urlencoded"}),
                timeout=TIMEOUT).read())
            notes.append("refresh_token grant works"
                         + (" (rotated)" if refreshed.get("refresh_token") else ""))
        except urllib.error.HTTPError as err:
            notes.append(f"refresh failed: HTTP {err.code} {err.read()[:160]!r}")
            ok = False

    # And the token has to be one oCIS accepts, with a personal space behind it.
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/graph/v1.0/me/drives",
        headers={"Authorization": "Bearer " + tokens["access_token"]})
    try:
        drives = json.loads(urllib.request.urlopen(request, timeout=TIMEOUT).read()).get("value", [])
        personal = next((d for d in drives if d.get("driveType") == "personal"), None)
        if personal:
            notes.append(f"oCIS accepts it: personal space '{personal.get('name')}'")
        else:
            notes.append(f"oCIS accepts it but there is no personal space among {len(drives)} drive(s)")
            ok = False
    except urllib.error.HTTPError as err:
        notes.append(f"oCIS rejected the token: HTTP {err.code} {err.read()[:160]!r}")
        ok = False

    return ok, notes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--issuer", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--environment", required=True, choices=sorted(CLIENTS))
    args = parser.parse_args()

    username = os.environ.get("AITY_CONTRACT_USER", "").strip()
    password = os.environ.get("AITY_CONTRACT_PASSWORD", "").strip()
    if not username or not password:
        print("AITY_CONTRACT_USER / AITY_CONTRACT_PASSWORD are not set "
              "(protected CI variables on the aity-cloud/drive group)", file=sys.stderr)
        return 2

    print(f"Aity Drive client-auth contract, {args.environment} "
          f"({args.issuer} -> {args.base_url})", flush=True)

    failures = []
    for client_id, redirect_uri in CLIENTS[args.environment]:
        print(f"\n{client_id}  ({redirect_uri})", flush=True)
        ok, notes = check_client(args.issuer, args.base_url, client_id,
                                 redirect_uri, username, password)
        for note in notes:
            print(f"  {'.' if ok else '!'} {note}", flush=True)
        if ok:
            print(f"  [PASS] {client_id}", flush=True)
        elif client_id in KNOWN_BLOCKED:
            print(f"  [KNOWN-BLOCKED] {client_id}: see "
                  f"drive/desktop/MAINTAINING.md 'Sync smoke gap'", flush=True)
        else:
            print(f"  [FAIL] {client_id}", flush=True)
            failures.append(client_id)

    print()
    if failures:
        print(f"CLIENT AUTH BROKEN: {', '.join(failures)}", flush=True)
        return 1
    print("client auth OK for every client that is not a known blocker", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
