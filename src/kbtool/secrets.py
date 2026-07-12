"""Secret scanning for KB content — a guardrail for public KBs.

Risk: an agent writes a credential into a KB whose site (or repo) is public.
This scans `docs/**/*.md` for likely secrets. On a **public** KB
(`kb.yml: visibility: public`) a high-confidence match is an **error** (fails
the deploy gate); on a private KB it is a **warning**, so you learn before you
ever flip the KB public. Softer signals (emails, generic key=value) are always
warnings.

Escape hatch: put `kbtool-allow-secret` anywhere on a line (e.g. a trailing
comment) to suppress findings for that line — for intentional examples.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import kb as kbmod

ALLOW_MARKER = "kbtool-allow-secret"

# High-confidence, structural / provider-specific — almost never intentional.
_HIGH: list[tuple[str, re.Pattern]] = [
    ("private key block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP |DSA )?PRIVATE KEY-----")),
    ("AWS access key id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[posru]_[A-Za-z0-9]{36,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("AWS secret access key", re.compile(r"(?i)aws.{0,20}['\"][0-9a-zA-Z/+]{40}['\"]")),
]

# Softer signals — often intentional (contact info, documented examples).
_MED: list[tuple[str, re.Pattern]] = [
    ("generic secret assignment", re.compile(
        r"(?i)\b(?:api[_-]?key|secret|token|password|passwd|access[_-]?key)\b\s*[:=]\s*"
        r"['\"]?[A-Za-z0-9/+_\-]{20,}['\"]?"
    )),
]

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
# Emails that are not personal-contact leaks: doc-example domains, VCS/tool
# handles, and noreply addresses.
_EMAIL_SAFE_DOMAINS = ("example.com", "example.org", "example.net")
_EMAIL_SAFE_LOCAL = ("git", "npm", "noreply")


def _personal_emails(line: str) -> list[str]:
    hits = []
    for m in _EMAIL_RE.finditer(line):
        addr = m.group(0)
        local, _, domain = addr.partition("@")
        if domain.lower().endswith(_EMAIL_SAFE_DOMAINS):
            continue
        if local.lower() in _EMAIL_SAFE_LOCAL or "noreply" in domain.lower():
            continue
        hits.append(addr)
    return hits


def scan(root: Path, is_public: bool) -> list[tuple[str, str, str, int]]:
    """Return (level, message, rel_path, line) tuples. level: error|warning."""
    out: list[tuple[str, str, str, int]] = []
    docs = root / "docs"
    if not docs.is_dir():
        return out
    for md in sorted(docs.rglob("*.md")):
        rel = md.relative_to(root).as_posix()
        for lineno, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            if ALLOW_MARKER in line:
                continue
            for label, rx in _HIGH:
                if rx.search(line):
                    lvl = "error" if is_public else "warning"
                    out.append((lvl, f"possible secret ({label}) in a "
                                f"{'PUBLIC' if is_public else 'private'} KB", rel, lineno))
            for label, rx in _MED:
                if rx.search(line):
                    out.append(("warning", f"{label} in content", rel, lineno))
            for addr in _personal_emails(line):
                out.append(("warning", f"personal email in content ({addr})", rel, lineno))
    return out
