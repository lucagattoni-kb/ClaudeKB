# Playbook: upgrade (bring this KB to a newer blueprint version)

The *installed* kbtool prints this, so procedure changes arrive one version
late. Any release-specific instructions are in the blueprint CHANGELOG read in
step 1 — always defer to it.

1. **Read the CHANGELOG** between this KB's current version
   (`.copier-answers.yml` → `_commit`) and the target tag. Note any breaking
   changes and content-migration playbooks.
2. **Update from the template** (copier is version-pinned so update semantics
   don't shift mid-fleet):
   `uvx copier==9.16.0 update --vcs-ref v<TARGET>`
   - Conflicts should appear **only** where the ownership boundary was
     violated (a KB-side edit to a blueprint-owned file). Resolve favouring
     the blueprint, then move the customization to a KB-owned file (or open a
     blueprint issue if none fits).
3. **Migrations**: copier `_migrations` run automatically for crossed
   versions. If the CHANGELOG lists a content-migration playbook (e.g. a
   frontmatter change across articles), run it now.
4. **Platform record**: if the CHANGELOG changed a canonical platform value
   (e.g. the build command), update BOTH the Cloudflare/GitHub dashboard and
   the `platform:` record in `kb.yml` (kb.yml is KB-owned — the upgrade will
   not touch it).
5. `uv run kbtool check && uv run kbtool build` — both must pass.
6. Commit with the blueprint version in the message; `uv run kbtool push`;
   append a `docs/log.md` entry
   `## <YYYYMMDD HH:MM> upgrade | blueprint v<TARGET>`.
