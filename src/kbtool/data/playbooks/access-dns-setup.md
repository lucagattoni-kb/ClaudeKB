# Playbook: access-dns-setup (Cloudflare Access for this KB)

Prerequisite: Cloudflare Zero Trust onboarding is done once for the account
(team name chosen). Every value set here must match the `platform:` record in
`kb.yml` (D17) — the repo is the source of truth, the dashboard is a cache.

**If `kb.yml: visibility: public`, skip steps 1–2 entirely** (no Access apps);
go straight to the verification checklist and confirm `/` returns 200 without
a login.

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

## Verification checklist (LIVE — do on the first KB, records resolve E4)

Run each probe and record the result in the blueprint's `docs/research/`:

- [ ] Anonymous GET `https://kb-<name>.example.com/` → Access login page.
- [ ] Anonymous GET `…/public/…` → 200 (bypass wins over the hostname app).
- [ ] `https://kb-<name>.<account>.workers.dev` → blocked / 404
      (workers.dev disabled — else Access can be bypassed).
- [ ] Anonymous GET the search index URL → login (private index confirmed).

If you prefer one wildcard Access app for `kb-*.example.com` instead of
per-KB apps, test that here and record the outcome.
