# Playbook: lint (scheduled KB health pass)

Run periodically (e.g. monthly per KB). Two passes — the first is mechanical,
the second is judgement.

## Structural pass (deterministic)

1. `uv run kbtool check` — resolve every error.
2. External-link sweep with lychee (not in the deploy gate, because
   external-site flakiness must never block a deploy):
   `lychee --no-progress 'docs/**/*.md'` — fix or annotate dead links.
3. Cross-KB (`kb://`) links: spot-check that referenced KBs/pages still exist
   (they are not resolvable at build time by design).

## Semantic pass (agent judgement, F3.2)

Read broadly and look for:
- **Contradictions** — two pages asserting incompatible facts.
- **Staleness** — claims that time has overtaken; update or mark
  `status: review`.
- **Orphans-in-spirit** — pages linked but conceptually disconnected;
  fold in or cross-link.
- **Missing cross-references** — related pages that should link to each other.
- **Gaps** — concepts referenced but never written up.

Fix what is unambiguous; file the rest as `status: review` pages or log
entries. Record the session in `docs/log.md`:
`## <YYYYMMDD HH:MM> lint | <summary of findings and actions>`.
