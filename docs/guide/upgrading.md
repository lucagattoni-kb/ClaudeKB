# Upgrading KBs

Blueprint improvements reach existing KBs through `copier update`. Each KB is
upgraded **independently** — there is no fleet-wide orchestration, so you can
upgrade one, verify, and stop if anything looks wrong.

## How a release works (blueprint side)

The blueprint is released with semver tags. Each release:

1. Finalizes a timestamped [CHANGELOG](../../CHANGELOG.md) entry (breaking vs
   non-breaking separated).
2. Bumps `__version__`, rebuilds the vendored wheel into the template, and
   regenerates the boundary checksums (`python scripts/release.py`).
3. Tags `vX.Y.Z` and pushes. CI verifies the template is in sync and that a KB
   scaffolded from the previous release upgrades to the new one with **zero
   conflicts**.

## Upgrading one KB

From inside the KB, the canonical procedure is `uv run kbtool playbook upgrade`.
In short:

1. **Read the CHANGELOG** between your current version
   (`.copier-answers.yml` → `_commit`) and the target tag. Note breaking
   changes and any content-migration steps.
2. **Update:**
   ```bash
   uvx copier==9.16.0 update --vcs-ref v<TARGET>
   ```
   Conflicts should appear **only** where the ownership boundary was violated
   (a KB-side edit to a blueprint-owned file). Resolve favouring the blueprint,
   then move the customization into a KB-owned file.
3. **Migrations.** Copier runs any mechanical migrations automatically. If the
   CHANGELOG lists a content-migration playbook (e.g. a frontmatter change
   across pages), run it now.
4. **Platform record.** If the release changed a canonical platform value
   (a build command, an Access app), update **both** the Cloudflare/GitHub
   dashboard **and** the `platform:` record in `kb.yml` — `kb.yml` is KB-owned,
   so the upgrade won't touch it silently.
5. **Gate and land:**
   ```bash
   uv lock && uv sync
   uv run kbtool check && uv run kbtool build
   git commit -am "Upgrade to blueprint v<TARGET>"
   uv run kbtool push
   ```
   Append a `docs/log.md` entry noting the upgrade.

## Why upgrades are safe

- **The ownership boundary is machine-enforced.** Blueprint-owned files are
  checksummed; editing one fails the gate, so upgrades can overwrite the
  plumbing without ever clobbering your content.
- **The vendored toolchain travels with the KB.** `copier update` swaps the old
  wheel for the new one atomically; a half-applied upgrade fails loudly on the
  next `uv run`.
- **CI proves it before you do.** Every release is tested by scaffolding from
  the prior tag and upgrading — a released upgrade that would conflict never
  ships.

The first real fleet upgrade (`kb-sandbox`, v0.1.0 → v0.1.1) landed with zero
conflicts, including a directory relocation — the machinery works as designed.

Next: [Roadmap](roadmap.md).
