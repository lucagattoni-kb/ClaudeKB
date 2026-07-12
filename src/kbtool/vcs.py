"""push / status (spec 6.1, D5 rebase-retry, F7.2 red-deploy detection)."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from pathlib import Path

from . import kb as kbmod


def push(root: Path, attempts: int = 3) -> int:
    for i in range(attempts):
        pull = kbmod.git(root, "pull", "--rebase", "--autostash")
        if pull.returncode != 0:
            print(pull.stderr.strip())
            print("ERROR: rebase failed — resolve conflicts and re-run `kbtool push`")
            return 1
        pushed = kbmod.git(root, "push")
        if pushed.returncode == 0:
            print(pushed.stderr.strip() or "pushed")
            return 0
        if i < attempts - 1:
            time.sleep(2 * (i + 1))
    print("ERROR: push still rejected after retries (remote moving fast?) — re-run `kbtool push`")
    return 1


def _github_owner_repo(root: Path) -> tuple[str, str] | None:
    url = kbmod.git(root, "remote", "get-url", "origin").stdout.strip()
    m = re.search(r"github\.com[:/]+([^/]+)/([^/.]+?)(?:\.git)?/?$", url)
    return (m.group(1), m.group(2)) if m else None


def _deploy_status_via_github(root: Path) -> str | None:
    """Read the Workers Builds result from the GitHub check-runs API.

    Agents run `gh`-authenticated but not `wrangler`-authenticated, so this is
    the reliable no-Cloudflare-credential path to red-deploy detection (F7.2).
    Returns a human line, or None if unavailable (caller falls back).
    """
    if shutil.which("gh") is None:
        return None
    orn = _github_owner_repo(root)
    if orn is None:
        return None
    owner, repo = orn
    sha = kbmod.git(root, "rev-parse", "HEAD").stdout.strip()
    proc = subprocess.run(
        ["gh", "api", f"repos/{owner}/{repo}/commits/{sha}/check-runs"],
        cwd=root, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return None
    try:
        runs = json.loads(proc.stdout).get("check_runs", [])
    except json.JSONDecodeError:
        return None
    builds = [
        r for r in runs
        if (r.get("app") or {}).get("slug") == "cloudflare-workers-and-pages"
        or "workers builds" in (r.get("name") or "").lower()
    ]
    if not builds:
        return "deploy status: no build check for HEAD yet (unpushed, or build still queued)"
    r = builds[0]
    concl = r.get("conclusion") or r.get("status")
    flag = "OK" if concl == "success" else f"** {str(concl).upper()} **"
    return f"deploy status ({r.get('name')}): {concl} {flag}"


def status(root: Path) -> int:
    # working tree
    st = kbmod.git(root, "status", "--porcelain")
    dirty = bool(st.stdout.strip())
    print("working tree:", "DIRTY" if dirty else "clean")
    if dirty:
        print(st.stdout.rstrip())

    # last deployment: prefer the GitHub check-runs API (no Cloudflare creds
    # needed — the path agents can actually use), then fall back to wrangler,
    # then to a dashboard nudge.
    gh_line = _deploy_status_via_github(root)
    if gh_line is not None:
        print(gh_line)
        return 0
    wrangler = "npx" if shutil.which("npx") else ("wrangler" if shutil.which("wrangler") else None)
    if wrangler is None:
        print("deploy status: unknown (no `gh` and no `wrangler` locally) — "
              "check the Cloudflare dashboard for the latest build result")
        return 0
    cmd = (["npx", "wrangler"] if wrangler == "npx" else ["wrangler"]) + ["deployments", "list"]
    proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    if proc.returncode != 0:
        print("deploy status: unknown (wrangler call failed) — check the Cloudflare dashboard")
        return 0
    print("deploy status (from `wrangler deployments list`):")
    for ln in [x for x in proc.stdout.splitlines() if x.strip()][:8]:
        print("  " + ln)
    return 0
