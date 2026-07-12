"""push / status (spec 6.1, D5 rebase-retry, F7.2 red-deploy detection)."""

from __future__ import annotations

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


def status(root: Path) -> int:
    # working tree
    st = kbmod.git(root, "status", "--porcelain")
    dirty = bool(st.stdout.strip())
    print("working tree:", "DIRTY" if dirty else "clean")
    if dirty:
        print(st.stdout.rstrip())

    # last deployment (best-effort; needs Node/wrangler + creds)
    if shutil.which("npx") is None and shutil.which("wrangler") is None:
        print("deploy status: unknown (wrangler/npx not available locally) — "
              "check the Cloudflare dashboard for the latest build result")
        return 0
    cmd = ["npx", "wrangler", "deployments", "list"] if shutil.which("npx") else ["wrangler", "deployments", "list"]
    proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    if proc.returncode != 0:
        print("deploy status: unknown (wrangler call failed) — check the Cloudflare dashboard")
        return 0
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    print("deploy status (most recent, from `wrangler deployments list`):")
    for ln in lines[:8]:
        print("  " + ln)
    return 0
