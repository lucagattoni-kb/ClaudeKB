"""kbtool verify-access — no-credential live access verification (D17).

Probes the deployed site anonymously (stdlib urllib, redirects not followed)
and asserts the behaviour matches this KB's `kb.yml`: `visibility` plus the
`platform.access_apps` record. This automates the launch checklist — "the repo
is the source of truth, the dashboard is a cache; verify they match" — with
zero Cloudflare credentials.
"""

from __future__ import annotations

import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from .kb import KbError, load_yaml

TIMEOUT = 15
ASSET_TOKEN = "__asset__"  # resolved at runtime by scraping an open page

_ASSET_RE = re.compile(r'(?:href|src)="([^"]*?/assets/[^"]*?\.(?:css|js))"')


@dataclass(frozen=True)
class Probe:
    path: str      # URL path, or ASSET_TOKEN
    expect: str    # "open" | "gated"
    why: str


def derive_probes(kb: dict) -> list[Probe]:
    """Pure derivation: kb.yml dict -> expected anonymous behaviour."""
    vis = str(kb.get("visibility", "private"))
    if vis == "public":
        return [Probe("/", "open", "visibility: public")]
    probes = [
        Probe("/", "gated", "visibility: private"),
        Probe("/search.json", "gated", "search index must stay private"),
    ]
    apps = (kb.get("platform") or {}).get("access_apps") or []
    for app in apps:
        path = app.get("path")
        if not path or not str(app.get("policy", "")).startswith("bypass"):
            continue
        norm = "/" + str(path).strip("/")
        if norm == "/assets":
            probes.append(Probe(ASSET_TOKEN, "open", "theme assets bypass (styled public pages)"))
        else:
            probes.append(Probe(norm + "/", "open", f"bypass app {app.get('name', norm)}"))
    return probes


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: N802
        return None


def _fetch(url: str) -> tuple[int, dict, bytes]:
    opener = urllib.request.build_opener(_NoRedirect)
    req = urllib.request.Request(url, headers={"User-Agent": "kbtool-verify-access"})
    try:
        with opener.open(req, timeout=TIMEOUT) as resp:
            return resp.status, dict(resp.headers), resp.read(65536)
    except urllib.error.HTTPError as e:
        # 3xx land here because the redirect handler refuses to follow
        return e.code, dict(e.headers), b""


def classify(status: int, headers: dict) -> str:
    """Observed anonymous behaviour: open | gated | other:<status>."""
    if status == 200:
        return "open"
    location = next((v for k, v in headers.items() if k.lower() == "location"), "")
    if status in (301, 302, 303, 307, 308) and "cloudflareaccess.com" in location:
        return "gated"
    if status in (401, 403):
        return "gated"
    return f"other:{status}"


def _resolve_asset_path(base: str, probes: list[Probe]) -> str | None:
    """Find a real theme-asset URL by scraping the first expected-open page."""
    for p in probes:
        if p.expect == "open" and p.path != ASSET_TOKEN:
            status, _, body = _fetch(base + p.path)
            if status != 200:
                continue
            m = _ASSET_RE.search(body.decode("utf-8", errors="replace"))
            if m:
                ref = m.group(1)
                # normalize ../assets/… or ./assets/… to /assets/…
                return "/assets/" + ref.split("/assets/", 1)[1]
    return None


def verify_access(root: Path) -> int:
    kb = load_yaml(root / "kb.yml")
    base = str(kb.get("url", "")).rstrip("/")
    if not base.startswith("https://"):
        raise KbError("kb.yml url must be an https URL")

    probes = derive_probes(kb)
    failures = 0
    for probe in probes:
        path = probe.path
        if path == ASSET_TOKEN:
            resolved = _resolve_asset_path(base, probes)
            if resolved is None:
                print(f"[FAIL] assets: could not discover a theme asset via an open page ({probe.why})")
                failures += 1
                continue
            path = resolved
        try:
            status, headers, _ = _fetch(base + path)
        except OSError as e:
            print(f"[FAIL] GET {path}: {e} (site not deployed, or DNS not ready?)")
            failures += 1
            continue
        got = classify(status, headers)
        ok = got == probe.expect
        print(f"[{'PASS' if ok else 'FAIL'}] GET {path} -> {got} (expected {probe.expect}; {probe.why})")
        if not ok:
            failures += 1

    if failures:
        print(f"\nverify-access: FAIL ({failures} mismatch(es)) — the live Access config "
              "does not match kb.yml. Fix the dashboard (see `kbtool playbook "
              "access-dns-setup`) or correct the kb.yml platform record.")
        return 1
    print("\nverify-access: OK — live behaviour matches kb.yml")
    return 0
