# Playbook: access-dns-setup (Cloudflare Access for this KB)

Prerequisite: Cloudflare Zero Trust onboarding is done once for the account
(team name chosen). Every value set here must match the `platform:` record in
`kb.yml` (D17) — the repo is the source of truth, the dashboard is a cache.

**If `kb.yml: visibility: public`, skip steps 1–3 entirely** (no Access apps);
run `uv run kbtool verify-access` to confirm `/` returns 200 without a login.

1. **Private app** — Cloudflare dashboard → Zero Trust → Access →
   Applications → Add (self-hosted):
   - Name: `kb-<name>`
   - Domain: `kb-<name>.example.com`
   - Policy: **Allow**, include → Emails → your email.
   - Identity provider: One-time PIN (default).
2. **Public bypass app** (only if the KB has a `docs/public/` subtree):
   - Name: `kb-<name>-public`
   - Domain: `kb-<name>.example.com`, path `/public`
   - Policy: **Bypass**, include → Everyone.
   - (Bypassed traffic is not logged — expected for public content.)
3. **Theme-assets bypass app** (required whenever step 2 is used — otherwise
   public pages load unstyled, because the theme's CSS/JS live at `/assets/`):
   - Name: `kb-<name>-assets`
   - Domain: `kb-<name>.example.com`, path `/assets`
   - Policy: **Bypass**, include → Everyone.
   - Safe: `/assets/` holds only generic theme files (KB media lives at
     `/media/`, which stays private). The search index (`/search.json`) and
     sitemap stay private, so no KB content leaks.

## Verification (automated)

```
uv run kbtool verify-access
```

Probes the live site anonymously and asserts behaviour matches this KB's
`kb.yml` (`visibility` + `platform.access_apps`): private paths and the search
index must redirect to Access login; each bypass path must return 200; a real
theme asset must load (so public pages render styled). Exit 0 = the live
config matches the repo record. On FAIL, fix the dashboard per the steps
above, or correct `kb.yml` if the record itself is wrong.

One probe it does not make: `https://kb-<name>.<account>.workers.dev` should
not resolve (workers.dev is disabled in wrangler.jsonc; verified account-wide
on KB #1 — re-check manually only if wrangler config changes).

If you prefer one wildcard Access app for `kb-*.example.com` instead of
per-KB apps, test that here and record the outcome.
