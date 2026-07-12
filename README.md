# ClaudeKB

**A blueprint for a fleet of self-sufficient, docs-as-code knowledge bases —
written and maintained primarily by AI agents.**

ClaudeKB is not a knowledge base itself. It is the **creator**: a
[copier](https://copier.readthedocs.io/) template plus a small Python
toolchain (`kbtool`) that scaffolds new KB repositories and upgrades existing
ones. Each generated KB is a standalone Git repo — Markdown content, strict
validation, and a one-command build/deploy — that an agent (or a human) can
write to via direct commits, published as a private-by-default static site
behind Cloudflare Access.

```
ClaudeKB (this repo)  ──scaffold──▶  kb-notes, kb-recipes, kb-… (one repo each)
      │  copier + kbtool wheel            │ agents write Markdown, push to main
      └──────── upgrade ◀─────────────────┘ Workers Builds gates + deploys
```

## Why it exists

Knowledge that AI agents both **read and write** wants to live as plain
Markdown in Git: diffable, reviewable, mergeable, and directly ingestible by
future retrieval layers — without a platform API in the way. ClaudeKB owns the
plumbing (schema enforcement, link/orphan checks, hosting, access control) once,
so every KB is consistent and every KB is independent. See
[What is ClaudeKB](docs/guide/what-is-claudekb.md) for the full rationale.

## Documentation

Start here, in order:

1. [What is ClaudeKB](docs/guide/what-is-claudekb.md) — purpose, model, and the
   ideas it's built on.
2. [Install & prerequisites](docs/guide/install.md) — tools and accounts you
   need.
3. [Create a KB](docs/guide/create-a-kb.md) — scaffold, build, deploy, and put
   it behind login.
4. [Using a KB](docs/guide/using-a-kb.md) — the day-to-day authoring workflow,
   commands, and conventions.
5. [Upgrading KBs](docs/guide/upgrading.md) — roll blueprint changes out across
   the fleet.
6. [Roadmap](docs/guide/roadmap.md) — what's next.

Going deeper:

- [Architecture spec](docs/architecture.md) — the full design and decision
  trail (`kbtool`, the ownership boundary, the build pipeline).
- [Requirements & decision record](REQUIREMENTS.md) — every decision (D1–D18)
  with rationale.
- [Research notes](docs/research/) — the OSS survey and experiments the design
  rests on.

## Status

`v0.1.1` — implemented and running. KB #1 (`kb-sandbox`) is live end-to-end:
scaffolded from the blueprint, gated by CI, deployed to Cloudflare Workers, and
protected by Cloudflare Access with a public subsection. See the
[CHANGELOG](CHANGELOG.md).

## Repository layout

- `src/kbtool/` — the toolchain source (the only home; D15). Built to a wheel,
  vendored into each KB.
- `template/` — the copier template a KB is scaffolded from.
- `playbooks/scaffold-kb.md` — the procedure that runs before a KB exists.
- `scripts/release.py` — builds the wheel into the template and regenerates
  the boundary checksums (blueprint-side only).
- `docs/` — this guide, the architecture spec, and research notes.

## License

See [LICENSE](LICENSE).
