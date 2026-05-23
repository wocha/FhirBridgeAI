#!/usr/bin/env python
"""OIDC end-to-end checks for dashboard OAuth2 flow."""

from __future__ import annotations

import html
import os
import re
import socket
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

BASE_URL = os.getenv("OIDC_BASE_URL", "https://dashboard.docker.localhost")
DASHBOARD_HOST = os.getenv("OIDC_DASHBOARD_HOST", "dashboard.docker.localhost")
KEYCLOAK_HOST = os.getenv("OIDC_KEYCLOAK_HOST", "keycloak.docker.localhost")
USERNAME = os.getenv("OIDC_E2E_USERNAME", "")
PASSWORD = os.getenv("OIDC_E2E_PASSWORD", "")
VERIFY_TLS = os.getenv("OIDC_VERIFY_TLS", "true").strip().lower() == "true"
ALLOW_INSECURE_DEV = os.getenv("OIDC_ALLOW_INSECURE_DEV", "false").strip().lower() == "true"
TIMEOUT = int(os.getenv("OIDC_E2E_TIMEOUT", "20"))

DEFAULT_CA_BUNDLE = Path(__file__).resolve().parents[2] / "certs" / "rootCA.pem"
CA_BUNDLE_PATH = Path(os.getenv("OIDC_CA_BUNDLE", str(DEFAULT_CA_BUNDLE))).resolve()

if not VERIFY_TLS and not ALLOW_INSECURE_DEV:
    raise SystemExit(
        "OIDC_VERIFY_TLS=false is blocked by default. "
        "Set OIDC_ALLOW_INSECURE_DEV=true explicitly for local dev exceptions."
    )

if VERIFY_TLS and not CA_BUNDLE_PATH.exists() and os.getenv("OIDC_CA_BUNDLE"):
    raise SystemExit(f"Configured OIDC_CA_BUNDLE does not exist: {CA_BUNDLE_PATH}")

REQUEST_VERIFY: bool | str = str(CA_BUNDLE_PATH) if VERIFY_TLS and CA_BUNDLE_PATH.exists() else VERIFY_TLS



def _patch_dns() -> None:
    original = socket.getaddrinfo

    def patched(host: str, port: int, *args, **kwargs):  # type: ignore[no-untyped-def]
        if host in {DASHBOARD_HOST, KEYCLOAK_HOST}:
            host = "127.0.0.1"
        return original(host, port, *args, **kwargs)

    socket.getaddrinfo = patched  # type: ignore[assignment]



def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)



def _redirect_to_auth(response: requests.Response) -> bool:
    location = response.headers.get("Location", "")
    return "/oauth2/start" in location or "/oauth2/sign_in" in location



def _is_signin_page(response: requests.Response) -> bool:
    return response.status_code == 403 and "<title>Sign In</title>" in response.text



def _extract_login_action(page_html: str, page_url: str) -> str:
    form_match = re.search(r'<form[^>]+id="kc-form-login"[^>]*action="([^"]+)"', page_html, flags=re.IGNORECASE)
    if not form_match:
        form_match = re.search(r'<form[^>]+action="([^"]+)"', page_html, flags=re.IGNORECASE)
    if not form_match:
        raise AssertionError("Could not find login form action in Keycloak page")
    return urljoin(page_url, html.unescape(form_match.group(1)))



def _extract_hidden_fields(page_html: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for name, value in re.findall(
        r'<input[^>]+type="hidden"[^>]+name="([^"]+)"[^>]+value="([^"]*)"',
        page_html,
        flags=re.IGNORECASE,
    ):
        fields[html.unescape(name)] = html.unescape(value)
    return fields



def _request(
    session: requests.Session,
    method: str,
    url: str,
    *,
    allow_redirects: bool = False,
    data: dict[str, str] | None = None,
) -> requests.Response:
    return session.request(
        method,
        url,
        data=data,
        allow_redirects=allow_redirects,
        timeout=TIMEOUT,
        verify=REQUEST_VERIFY,
    )



def check_missing_headers(session: requests.Session) -> None:
    response = _request(session, "GET", BASE_URL)
    ok_redirect = response.status_code in {302, 303, 307} and _redirect_to_auth(response)
    ok_signin = _is_signin_page(response)
    _assert(ok_redirect or ok_signin, f"unexpected unauthenticated response status={response.status_code}")
    print("[PASS] Missing-header request is challenged by oauth2-proxy")



def check_forged_headers(session: requests.Session) -> None:
    forged = {
        "X-Forwarded-User": "attacker",
        "X-Forwarded-Groups": "auditor",
        "X-Auth-Request-User": "attacker",
    }
    response = session.get(
        BASE_URL,
        headers=forged,
        allow_redirects=False,
        timeout=TIMEOUT,
        verify=REQUEST_VERIFY,
    )
    ok_redirect = response.status_code in {302, 303, 307} and _redirect_to_auth(response)
    ok_signin = _is_signin_page(response)
    _assert(ok_redirect or ok_signin, f"forged-header response status={response.status_code}")
    print("[PASS] Forged headers do not bypass oauth2-proxy")



def check_successful_login_and_callback(session: requests.Session) -> None:
    _assert(bool(USERNAME and PASSWORD), "OIDC_E2E_USERNAME and OIDC_E2E_PASSWORD must be set")

    start = _request(session, "GET", f"{BASE_URL.rstrip('/')}/oauth2/start?rd=%2F")
    _assert(start.status_code in {302, 303, 307}, f"unexpected oauth2/start status: {start.status_code}")

    keycloak_auth_url = start.headers.get("Location", "")
    _assert("openid-connect/auth" in keycloak_auth_url, "oauth2/start did not redirect to keycloak")

    login_page = _request(session, "GET", keycloak_auth_url)
    _assert(login_page.status_code == 200, f"unexpected keycloak login page status: {login_page.status_code}")

    action_url = _extract_login_action(login_page.text, keycloak_auth_url)
    payload = _extract_hidden_fields(login_page.text)
    payload.update({"username": USERNAME, "password": PASSWORD})

    current = _request(session, "POST", action_url, data=payload)
    callback_statuses: list[int] = []

    for _ in range(12):
        parsed = urlparse(current.url)
        if "/oauth2/callback" in parsed.path:
            callback_statuses.append(current.status_code)

        if current.status_code not in {301, 302, 303, 307, 308}:
            break

        location = current.headers.get("Location")
        _assert(bool(location), "redirect without location header")
        current = _request(session, "GET", urljoin(current.url, location))

    _assert(current.status_code not in {500, 403}, f"post-login terminal status={current.status_code}")
    _assert("Invalid username or password" not in current.text, "Keycloak rejected credentials")
    _assert(callback_statuses, "callback endpoint was not reached during login flow")
    _assert(all(code not in {500, 403} for code in callback_statuses), "callback returned 500/403")

    dashboard = _request(session, "GET", BASE_URL)
    _assert(dashboard.status_code not in {500, 403}, f"protected dashboard status={dashboard.status_code}")
    print("[PASS] Successful OIDC flow completed without callback 500/403 regression")



def main() -> int:
    _patch_dns()
    session = requests.Session()
    print(
        f"OIDC TLS mode: verify={'true' if VERIFY_TLS else 'false'}; "
        f"ca_bundle={CA_BUNDLE_PATH if VERIFY_TLS else 'n/a'}"
    )

    try:
        check_missing_headers(session)
        check_forged_headers(session)
        check_successful_login_and_callback(session)
    except Exception as exc:
        print(f"OIDC E2E check failed: {exc}")
        return 1

    print("OIDC E2E checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

