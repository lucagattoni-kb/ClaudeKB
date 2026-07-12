#!/usr/bin/env python3
"""Blueprint-side release helper (spec §8, §12.3). NOT a kbtool command — a KB
must not be able to regenerate its own boundary manifest and whitewash drift.

Builds the kbtool wheel into template/vendor/, stamps the version into the
templated managed files, and regenerates template/blueprint-checksums.json.

Usage:
    python scripts/release.py            # stamp current __version__
    python scripts/release.py --check    # verify template is in sync (CI)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "template"

# KB-root-relative paths. Static (rendered == template) → checksummed.
# Templated (per-KB values) → managed-marker checked instead.
CHECKSUM_FILES = [".gitattributes", ".gitignore", "CLAUDE.md"]  # + the wheel
MARKED_FILES = ["wrangler.jsonc", "pyproject.toml"]


def read_version() -> str:
    text = (ROOT / "src" / "kbtool" / "__init__.py").read_text()
    m = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    if not m:
        sys.exit("cannot find __version__ in src/kbtool/__init__.py")
    return m.group(1)


def build_wheel_into(vendor: Path) -> str:
    """Build the wheel from src/ into `vendor/` (clearing old wheels). Returns filename."""
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(
            ["uv", "build", "--wheel", "-o", td],
            cwd=ROOT, check=True, capture_output=True, text=True,
        )
        wheels = list(Path(td).glob("kbtool-*.whl"))
        if len(wheels) != 1:
            sys.exit(f"expected exactly one wheel, got {wheels}")
        wheel = wheels[0]
        vendor.mkdir(exist_ok=True)
        for old in vendor.glob("*.whl"):
            old.unlink()
        shutil.copy2(wheel, vendor / wheel.name)
        return wheel.name


def build_wheel(version: str) -> str:
    return build_wheel_into(TEMPLATE / "vendor")


def manifest_for(base: Path, version: str, wheel_name: str) -> dict:
    checksums = {rel: sha256(base / rel) for rel in CHECKSUM_FILES}
    checksums[f"vendor/{wheel_name}"] = sha256(base / "vendor" / wheel_name)
    return {"blueprint_version": version, "checksums": checksums, "marked_files": MARKED_FILES}


def sync_dir(fixture: Path) -> int:
    """Rebuild the wheel from src/ into a scaffolded fixture and regen its
    checksum manifest (spec §12.1 — CI never trusts the committed wheel)."""
    version = read_version()
    wheel_name = build_wheel_into(fixture / "vendor")
    (fixture / "blueprint-checksums.json").write_text(
        json.dumps(manifest_for(fixture, version, wheel_name), indent=2) + "\n"
    )
    print(f"sync-dir: {fixture} synced to v{version} ({wheel_name})")
    return 0


def stamp_templates(version: str, wheel_name: str) -> None:
    pyproj = TEMPLATE / "pyproject.toml.jinja"
    t = pyproj.read_text()
    t = re.sub(r"MANAGED BY BLUEPRINT v[\d.]+", f"MANAGED BY BLUEPRINT v{version}", t)
    t = re.sub(r'kbtool==[\d.]+', f"kbtool=={version}", t)
    t = re.sub(r'vendor/kbtool-[\d.]+-py3-none-any\.whl', f"vendor/{wheel_name}", t)
    pyproj.write_text(t)

    wrangler = TEMPLATE / "wrangler.jsonc.jinja"
    w = wrangler.read_text()
    w = re.sub(r"MANAGED BY BLUEPRINT v[\d.]+", f"MANAGED BY BLUEPRINT v{version}", w)
    wrangler.write_text(w)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_manifest(version: str, wheel_name: str) -> dict:
    return manifest_for(TEMPLATE, version, wheel_name)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify sync without writing")
    ap.add_argument("--sync-dir", type=Path, help="rebuild wheel + checksums into a scaffolded fixture")
    args = ap.parse_args()

    if args.sync_dir:
        return sync_dir(args.sync_dir.resolve())

    version = read_version()

    if args.check:
        wheels = list((TEMPLATE / "vendor").glob("*.whl"))
        if len(wheels) != 1:
            print(f"FAIL: expected one vendored wheel, found {wheels}")
            return 1
        manifest = build_manifest(version, wheels[0].name)
        on_disk = json.loads((TEMPLATE / "blueprint-checksums.json").read_text())
        if on_disk != manifest:
            print("FAIL: blueprint-checksums.json out of sync with template — run scripts/release.py")
            return 1
        if wheels[0].name != f"kbtool-{version}-py3-none-any.whl":
            print(f"FAIL: vendored wheel {wheels[0].name} != version {version}")
            return 1
        print(f"release --check: OK (v{version})")
        return 0

    wheel_name = build_wheel(version)
    stamp_templates(version, wheel_name)
    manifest = build_manifest(version, wheel_name)
    (TEMPLATE / "blueprint-checksums.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    print(f"release: stamped v{version}, wheel {wheel_name}, checksums regenerated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
