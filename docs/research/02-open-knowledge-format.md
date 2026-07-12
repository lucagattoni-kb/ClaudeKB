# Open Knowledge Format (OKF) — analysis for ClaudeKB

> Research doc. Analyzed 20260712 against the normative SPEC.md (v0.1, Google,
> June 2026). Confidence: high — spec is one page and was read directly.

## What it is

A vendor-neutral spec (GoogleCloudPlatform/knowledge-catalog) formalizing the
"knowledge as a directory of Markdown files with YAML frontmatter" pattern so
that bundles written by one producer are consumable by any agent. Explicitly
inspired by the llm-wiki pattern (see doc 03). v0.1, June 2026 — very young,
but backed by Google Cloud and already has third-party tooling (a CLI:
openknowledge-sh/openknowledge) and curated lists.

## Normative content (v0.1)

- **Required frontmatter**: exactly one field — `type` (free-form string,
  no central registry; consumers must tolerate unknown types).
- **Recommended**: `title`, `description`, `resource` (URI of the underlying
  asset, for concept docs describing external things), `tags` (list),
  `timestamp` (ISO 8601 of last meaningful change).
- **Custom keys allowed**; consumers must preserve unknown fields and never
  reject documents for having them.
- **Reserved filenames**: `index.md` (directory listing, progressive
  disclosure, no frontmatter) and `log.md` (chronological change history,
  ISO-date groupings). Everything else `.md` is a concept document.
- **Bundle** = self-contained directory tree; distribution via git repo
  (recommended), archive, or subdirectory.
- **Links**: bundle-root-absolute (`/...`, recommended for stability) or
  relative. Broken links are tolerated by consumers.
- **Conformance**: parseable frontmatter everywhere + non-empty `type` +
  reserved files follow their structure. Everything else is soft guidance.

## Findings

- **F2.1 — Our frontmatter D6 is one field away from OKF conformance.** We
  require `title` + `description`; OKF requires `type`. Adding a required
  `type` (validated against a per-KB vocabulary, like tags) makes every KB an
  OKF-conformant bundle at near-zero cost — free interop with a growing
  agent-tooling ecosystem, and `type` is genuinely useful for agents deciding
  how to read a page (article vs. reference vs. playbook vs. log).
- **F2.2 — OKF's permissive-consumer stance conflicts with our strict-CI
  stance — resolve by splitting roles.** OKF says consumers tolerate broken
  links and unknown fields; ClaudeKB CI is strict at *write/build* time.
  These compose cleanly: strict as producer, permissive as consumer. Our
  validators enforce more than OKF requires; the *output* stays conformant.
- **F2.3 — `index.md` + `log.md` conventions match the llm-wiki pattern and
  are worth reserving in the blueprint** even if `log.md` starts unused:
  agents get a standard place for progressive disclosure and change
  narrative. Caveat: our `index.md` will carry frontmatter (site needs
  title); OKF says reserved files have *no* frontmatter — check whether that
  breaks conformance or is soft guidance (it is listed under reserved-file
  structure → likely hard). Possible out: OKF `index.md` is optional; a KB
  can use `catalog.md` for the agent-facing listing if conflict is real.
- **F2.4 — `timestamp` (recommended, not required) is compatible with D6's
  git-derived dates**: we can inject it at build/export time rather than
  storing it in source frontmatter. Conformance is judged on the bundle we
  publish/export, not on our authoring flow.
- **F2.5 — Bundle-root-absolute links** are OKF's stability recommendation;
  matches our need for stable intra-KB links and gives cross-KB links a clean
  boundary (bundle = KB; cross-KB = full URL under the `kb-<name>` scheme).

## Adopt / adapt / avoid

- **Adopt**: required `type` field (pending Luca's decision — changes D6);
  `index.md`/`log.md` reservations; bundle-root-absolute link convention.
- **Adapt**: strict-producer/permissive-consumer split (F2.2); build-time
  `timestamp` injection (F2.4).
- **Avoid**: nothing — the spec is small enough that partial adoption doesn't
  drag dependencies in.

## Gaps / next loop

- Verify the `index.md` no-frontmatter rule's strictness against SPEC.md
  wording (F2.3) before wiring conventions.
- Watch OKF evolution (v0.1 → v1): joining now means tracking a moving spec.

## Sources

- https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md
- https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing/
- https://github.com/openknowledge-sh/openknowledge
