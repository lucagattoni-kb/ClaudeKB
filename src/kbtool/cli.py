"""kbtool command-line entry point (spec 6.1)."""

from __future__ import annotations

import argparse
import sys
from importlib import resources
from pathlib import Path

from . import __version__
from .kb import KbError, find_kb_root

PLAYBOOKS = ("upgrade", "ingest", "lint", "access-dns-setup")


def run_check(root: Path) -> int:
    from .validators import run_all

    findings = run_all(root)
    errors = [f for f in findings if f.level == "error"]
    warnings = [f for f in findings if f.level == "warning"]
    for f in warnings:
        print(f.format())
    for f in errors:
        print(f.format())
    if errors:
        print(f"\nkbtool check: FAIL ({len(errors)} error(s), {len(warnings)} warning(s))")
        return 1
    print(f"kbtool check: OK ({len(warnings)} warning(s))")
    return 0


def cmd_playbook(name: str) -> int:
    if name not in PLAYBOOKS:
        print(f"unknown playbook '{name}'. Available: {', '.join(PLAYBOOKS)}", file=sys.stderr)
        return 2
    text = resources.files("kbtool.data.playbooks").joinpath(f"{name}.md").read_text()
    print(text)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="kbtool", description="ClaudeKB toolchain")
    parser.add_argument("--version", action="version", version=f"kbtool {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="run all validators (deploy gate)")
    sub.add_parser("build", help="check, preprocess, and build the site")
    sub.add_parser("serve", help="preprocess and serve a live preview")
    sub.add_parser("ci", help="alias of build; the Workers Builds entry point")
    sub.add_parser("push", help="rebase-retry push (D5)")
    sub.add_parser("status", help="report deploy result + working-tree state")
    pb = sub.add_parser("playbook", help="print a version-matched procedure")
    pb.add_argument("name", choices=PLAYBOOKS)

    args = parser.parse_args(argv)

    if args.cmd == "playbook":
        return cmd_playbook(args.name)

    try:
        root = find_kb_root()
    except KbError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    try:
        if args.cmd == "check":
            return run_check(root)
        if args.cmd in ("build", "ci"):
            from .build import build
            return build(root)
        if args.cmd == "serve":
            from .build import serve
            return serve(root)
        if args.cmd == "push":
            from .vcs import push
            return push(root)
        if args.cmd == "status":
            from .vcs import status
            return status(root)
    except KbError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
