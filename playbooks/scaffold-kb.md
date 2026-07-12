# Playbook: scaffold a new KB

The one procedure that runs before a KB exists, so it lives in the blueprint
(not in the kbtool package). All other procedures ship inside kbtool
(`uv run kbtool playbook <name>`).

## One-time prerequisites (first KB only)

1. Create the GitHub org for the fleet (D1) and transfer this blueprint repo
   into it (GitHub auto-redirects the old URL).
2. Install/authorize the **Cloudflare Workers and Pages** GitHub app for the org.
3. Complete Cloudflare Zero Trust onboarding once (choose the team name) — no
   Access app can exist until this is done.

## Per-KB

Replace `<name>`, `<title>`, `<desc>`, `<VERSION>` (latest blueprint tag).

1. `gh repo create <org>/kb-<name> --private`
2. Scaffold (copier pinned so update semantics don't shift mid-fleet):
   ```
   uvx copier==9.16.0 copy --vcs-ref v<VERSION> gh:<org>/ClaudeKB kb-<name> \
     -d kb_domain=<domain> -d kb_name=<name> -d kb_title="<title>" -d kb_description="<desc>"
   cd kb-<name>
   uv lock && git init -b main && git add -A && git commit -m "scaffold kb-<name>"
   ```
3. Gate locally — must pass before the first push:
   `uv run kbtool check && uv run kbtool build`
4. Push and wire deploy:
   ```
   git remote add origin git@github.com:<org>/kb-<name>.git
   uv run kbtool push
   ```
   In the Cloudflare dashboard: Workers & Pages → create → import the repo →
   set build command `uv run kbtool ci`, deploy command `npx wrangler deploy`,
   branch `main`. These must match the `platform:` record in `kb.yml` (D17).
   The first deploy creates the custom domain + DNS record automatically.
5. Cloudflare Access: `uv run kbtool playbook access-dns-setup` and follow it,
   including the LIVE verification checklist (first KB resolves the open E4
   probes — record results in this blueprint's `docs/research/`).
6. Append a scaffold entry to the KB's `docs/log.md`. Nothing is registered
   centrally — the fleet is discoverable via each repo's `kb.yml`.

## Notes

- uv availability in the Workers Builds image is unverified. If the build fails
  with "uv: not found", prepend to the build command:
  `curl -LsSf https://astral.sh/uv/install.sh | sh &&`.
