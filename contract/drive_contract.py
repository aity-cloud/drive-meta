#!/usr/bin/env python3
"""Tier 1 end-to-end test: the server contract the Aity Drive Clients depend on.

WHY THIS EXISTS. On 2026-08-27 the iOS client logged in and then sat with an
account that never loaded. The cause was server-side and entirely invisible
to the app: oCIS 8 stamps a last-sign-in time onto the user's LDAP entry, our
schema had no such attribute, and `/graph/v1.0/me` answered 500 on alternate
requests. Production had been doing it ~17 times a day, unnoticed, since the
oCIS 8 upgrade. A UI test would not have found it quickly; this walks exactly
the request sequence a client makes and fails loudly on the first thing that
is not what a client needs.

It is deliberately dependency-free (python3 stdlib only) so it runs in the
plain catalog alpine image, and it is read-mostly: the only writes are a
single file it creates and deletes inside the test user's own personal space.

Usage:
    drive_contract.py --base-url https://drive.aity.works \\
                      --issuer   https://auth.aity.works/realms/aity \\
                      --client-id drive

Credentials come from the environment (protected CI variables):
    AITY_CONTRACT_USER, AITY_CONTRACT_PASSWORD

Exit code 0 = every check passed. Non-zero = the first failure is printed
with what was expected, what came back, and why a client cares.
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, field

TIMEOUT = 30


@dataclass
class Result:
    checks: list = field(default_factory=list)

    def record(self, name: str, ok: bool, detail: str) -> bool:
        self.checks.append((name, ok, detail))
        marker = "PASS" if ok else "FAIL"
        print(f"  [{marker}] {name}: {detail}", flush=True)
        return ok

    @property
    def failed(self) -> list:
        return [c for c in self.checks if not c[1]]


def request(method: str, url: str, token: str | None = None, body: bytes | None = None,
            headers: dict | None = None):
    """Returns (status, headers, body-bytes). Never raises on HTTP status."""
    req = urllib.request.Request(url, method=method, data=body)
    req.add_header("User-Agent", "aity-drive-contract/1.0")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as err:
        return err.code, dict(err.headers or {}), err.read()
    except Exception as err:  # network, TLS, DNS
        return 0, {}, str(err).encode()


def get_token(issuer: str, client_id: str, username: str, password: str) -> tuple[str | None, str]:
    payload = urllib.parse.urlencode({
        "client_id": client_id,
        "grant_type": "password",
        "scope": "openid profile email",
        "username": username,
        "password": password,
    }).encode()
    status, _, body = request(
        "POST", f"{issuer}/protocol/openid-connect/token", body=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if status != 200:
        return None, f"HTTP {status}: {body[:200].decode('utf-8', 'replace')}"
    data = json.loads(body)
    return data.get("access_token"), f"token acquired ({len(data.get('access_token',''))} chars)"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True, help="e.g. https://drive.aity.works")
    parser.add_argument("--issuer", required=True, help="e.g. https://auth.aity.works/realms/aity")
    parser.add_argument("--client-id", default="drive")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    username = os.environ.get("AITY_CONTRACT_USER", "").strip()
    password = os.environ.get("AITY_CONTRACT_PASSWORD", "").strip()
    if not username or not password:
        print("AITY_CONTRACT_USER / AITY_CONTRACT_PASSWORD are not set "
              "(protected CI variables on the aity-cloud/drive group)", file=sys.stderr)
        return 2

    print(f"Aity Drive contract test against {base}", flush=True)
    result = Result()

    # 1. Discovery, exactly as a client bootstraps a new account.
    status, _, body = request("GET", f"{base}/.well-known/webfinger?resource=acct:me@{urllib.parse.urlparse(base).netloc}")
    result.record("webfinger", status in (200, 404),
                  f"HTTP {status} (404 is acceptable - clients fall back to the base URL)")

    status, _, body = request("GET", f"{base}/status.php")
    ok = status == 200 and b"installed" in body
    result.record("status.php", ok, f"HTTP {status} {body[:80].decode('utf-8','replace')}")

    # 2. Authenticate the way the apps do.
    token, detail = get_token(args.issuer, args.client_id, username, password)
    if not result.record("oidc password grant", token is not None, detail):
        print("\nWithout a token nothing below can run.", file=sys.stderr)
        return 1

    # 3. The calls the clients make immediately after login. `/graph/v1.0/me`
    #    is the one that broke on 2026-08-27 - it is the account itself.
    status, _, body = request("GET", f"{base}/ocs/v2.php/cloud/capabilities?format=json", token)
    result.record("capabilities", status == 200, f"HTTP {status}, {len(body)} bytes")

    status, _, body = request("GET", f"{base}/graph/v1.0/me", token)
    me = json.loads(body) if status == 200 and body[:1] == b"{" else {}
    ok = status == 200 and bool(me.get("id"))
    result.record("graph /me", ok,
                  f"HTTP {status} id={me.get('id','-')} name={me.get('displayName','-')}")

    status, _, body = request("GET", f"{base}/graph/v1.0/me/drives", token)
    drives = json.loads(body).get("value", []) if status == 200 and body[:1] == b"{" else []
    personal = next((d for d in drives if d.get("driveType") == "personal"), None)
    result.record("graph /me/drives", personal is not None,
                  f"HTTP {status}, {len(drives)} drive(s), personal={'yes' if personal else 'NO'}")
    if not personal:
        print("\nNo personal space: a client has nothing to open, which looks "
              "like 'the account does not load'.", file=sys.stderr)
        return 1

    # The client follows the URL the SERVER advertises. If that is wrong or
    # unreachable, the app goes quiet without an error - worth asserting.
    webdav = (personal.get("root") or {}).get("webDavUrl") or ""
    result.record("personal space advertises a WebDAV URL",
                  webdav.startswith(base),
                  f"{webdav or '(none)'} (must start with {base})")

    # 4. A real round trip in the user's own space: list, upload, read back,
    #    delete. This is what 'the files show up' actually means.
    status, _, body = request("PROPFIND", webdav, token,
                              headers={"Depth": "1", "Content-Type": "application/xml"})
    result.record("PROPFIND personal space", status in (207, 200), f"HTTP {status}, {len(body)} bytes")

    name = f"aity-contract-{uuid.uuid4().hex[:8]}.txt"
    payload = f"aity drive contract test {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n".encode()
    status, _, _ = request("PUT", f"{webdav.rstrip('/')}/{name}", token, body=payload,
                           headers={"Content-Type": "text/plain"})
    uploaded = result.record("PUT a file", status in (201, 204), f"HTTP {status} {name}")

    if uploaded:
        # oCIS answers 425 Too Early while the upload is still being
        # post-processed (antivirus, thumbnails). That is correct server
        # behaviour and every client retries, so the test does too - failing
        # on the first 425 would make this permanently red for no reason.
        deadline = time.time() + 60
        attempts = 0
        while True:
            attempts += 1
            status, _, got = request("GET", f"{webdav.rstrip('/')}/{name}", token)
            if status != 425 or time.time() > deadline:
                break
            time.sleep(2)
        result.record("GET it back", status == 200 and got == payload,
                      f"HTTP {status} after {attempts} attempt(s), "
                      f"{'identical bytes' if got == payload else 'CONTENT DIFFERS'}")

        status, _, _ = request("DELETE", f"{webdav.rstrip('/')}/{name}", token)
        result.record("DELETE it (leave no litter)", status in (204, 200), f"HTTP {status}")

    print()
    if result.failed:
        print(f"CONTRACT BROKEN: {len(result.failed)} of {len(result.checks)} checks failed", flush=True)
        for name, _, detail in result.failed:
            print(f"  - {name}: {detail}")
        return 1

    print(f"contract OK: {len(result.checks)} checks passed", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
