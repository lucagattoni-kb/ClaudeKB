# docs/research — OSS KB-as-code analysis (loop 1, 20260712)

Per-project analysis docs feeding the ClaudeKB blueprint design. Read
`SYNTHESIS.md` first — it ranks the findings (cited as F<doc>.<n>) and lists
the decision checkpoint. Each project doc states its confidence level and the
gaps the next research loop must close.

| Doc | Subject | One-line takeaway |
|---|---|---|
| [SYNTHESIS.md](SYNTHESIS.md) | Cross-project synthesis | D9 falsified; copier ≈ §4 engine; validators must be SSG-independent |
| [01](01-zensical-and-the-mkdocs-collapse.md) | Zensical & MkDocs collapse | SSG default is dead; successor decision + swappability required |
| [02](02-open-knowledge-format.md) | Open Knowledge Format | `type` field away from free agent-ecosystem interop |
| [03](03-llm-wiki-pattern.md) | llm-wiki pattern | KB-CLAUDE.md schema layer + ingest/query/lint workflows |
| [04](04-copier-scaffolding.md) | copier vs cruft | Blueprint scaffold/upgrade engine, pending conflict test |
| [05](05-antora.md) | Antora | Stable logical IDs beat stable URLs; aggregate later |
| [06](06-quartz.md) | Quartz | Backlinks are the reader-UX gap worth closing |
| [07](07-gitlab-handbook.md) | GitLab Handbook | Tuned lint configs; feedback at the point of write |
| [08](08-backstage-techdocs.md) | Backstage TechDocs | Per-KB manifest; platform-owned build entry point |
| [09](09-basic-memory.md) | Basic Memory | MCP-over-Markdown validated; maybe reuse, don't build |
