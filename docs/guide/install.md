# Install & prerequisites

ClaudeKB is Python-native and uses [uv](https://docs.astral.dev/uv/) for
everything. You install almost nothing globally — `uv` manages the rest per
project, and each KB vendors its own toolchain.

## Tools

| Tool | Why | Install |
|---|---|---|
| **uv** | Runs the toolchain, manages Python + deps per KB | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **git** | Everything is Git | your OS package manager |
| **copier** (via `uvx`) | Scaffolds/upgrades KBs — no global install needed | invoked as `uvx copier@9.16.0 …` |
| **gh** (GitHub CLI) | Creating KB repos | `brew install gh` (or your OS) |
| **Node/npx** | Only for `wrangler` at deploy time (handled by CI) | optional locally |

You do **not** install `kbtool` globally. Each KB carries it as a vendored
wheel and runs it with `uv run kbtool …`; `uv` installs it into the KB's
virtual environment on first run.

## Accounts (one-time, for hosting)

Hosting is on Cloudflare's free tier. First KB only:

1. **A GitHub organization** for the fleet (keeps KB repos separate from your
   personal repos). Create it at
   [github.com/organizations/new](https://github.com/organizations/new) (free
   plan).
2. **The blueprint repo transferred into that org** — one home for the whole
   fleet; the Cloudflare Workers Builds GitHub app then scopes to a single org.
3. **A Cloudflare account with your domain** already on Cloudflare (for the
   `kb-<name>.<your-domain>` hostnames — free Universal SSL covers one
   subdomain level). You pass this domain once per KB via the `kb_domain`
   scaffold answer (see [Create a KB](create-a-kb.md)); it's stored per-KB and
   reused on upgrades.
4. **Cloudflare Zero Trust onboarded once** (pick a team name) — required before
   any Access application can exist. The free plan covers 50 users.

The exact click-path for the Cloudflare side is in
[Create a KB](create-a-kb.md), step 4.

## Working on the blueprint itself

If you're developing the blueprint (not just using it):

```bash
git clone <blueprint-repo> && cd ClaudeKB
uv run --with pytest pytest tests/     # unit tests
bash tests/run_e2e.sh                  # scaffold → gate → no-op update
```

After changing `src/kbtool/` or any `template/` file, run
`python scripts/release.py` to rebuild the vendored wheel and regenerate the
boundary checksums, then commit. See [CLAUDE.md](../../CLAUDE.md) for the full
contributor rules.

Next: [Create a KB](create-a-kb.md).
