# ClaudeKB blueprint

Blueprint (creator) for a fleet of self-sufficient, docs-as-code knowledge
bases. See `docs/architecture.md` for the full spec and `REQUIREMENTS.md`
for the decision record (D1–D18).

- `src/kbtool/` — the only home of the KB toolchain source (D15). Built to a
  wheel and vendored into each KB.
- `template/` — the copier template a KB is scaffolded from.
- `playbooks/scaffold-kb.md` — the one procedure that runs before a KB exists.
- `scripts/release.py` — builds the wheel into the template and regenerates
  the boundary checksums (blueprint-side only).

To scaffold a KB, see `playbooks/scaffold-kb.md`.
