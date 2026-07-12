# Create a KB

This walks through scaffolding a new KB, gating it locally, pushing it, and
putting it online behind a login. The canonical, always-current version of
these steps ships inside the toolchain — run
`uv run kbtool playbook access-dns-setup` from a KB for the Cloudflare part.

Throughout, replace `<name>` with your KB slug (lowercase letters, digits,
hyphens), and `<org>` with your fleet's GitHub org.

## 1. Scaffold

```bash
gh repo create <org>/kb-<name> --private
uvx copier@9.16.0 copy --vcs-ref v0.1.1 gh:<org>/ClaudeKB kb-<name> \
  -d kb_name=<name> -d kb_title="<Title>" -d kb_description="<one sentence>"
cd kb-<name>
uv lock && git init -b main && git add -A && git commit -m "scaffold kb-<name>"
```

`--vcs-ref` pins the blueprint version — always scaffold from a released tag,
never a branch. The scaffold produces a complete KB: content skeleton, nav,
vocabulary, the vendored toolchain, and deploy config.

## 2. Gate locally

```bash
uv run kbtool check   # all validators must pass
uv run kbtool build   # produces .build/site
```

Both must be green **before** you push. `kbtool serve` gives a live local
preview.

## 3. Push and wire the deploy

```bash
git remote add origin git@github.com:<org>/kb-<name>.git
uv run kbtool push
```

In the Cloudflare dashboard → **Workers & Pages → Create → Import a
repository**, pick `kb-<name>` and set:

- **Build command:** `uv run kbtool ci`
- **Deploy command:** `npx wrangler deploy`
- **Branch:** `main`, **Root directory:** `/`

Save and deploy. Cloudflare runs the same gate as your local one, then deploys;
the first deploy **auto-creates** the custom domain `kb-<name>.<your-domain>`
and its DNS record. (`uv` is preinstalled in the build image — no extra setup.)

## 4. Put it behind login (Cloudflare Access)

Run `uv run kbtool playbook access-dns-setup` and follow it. In short, in
Zero Trust → Access → Applications, create **self-hosted** apps:

| App | Hostname / path | Policy |
|---|---|---|
| `kb-<name>` | `kb-<name>.<domain>` | **Allow** → your email (one-time PIN) |
| `kb-<name>-public` | `kb-<name>.<domain>` path `/public` | **Bypass** → Everyone |
| `kb-<name>-assets` | `kb-<name>.<domain>` path `/assets` | **Bypass** → Everyone |

The `/public` app makes your public subsection world-readable; the `/assets`
app lets those public pages load the theme's CSS/JS (otherwise they render
unstyled). Your KB content images live at `/media/` and stay private. If the KB
is fully public (`kb.yml: visibility: public`), skip all three apps.

Skip step 4 entirely if you didn't add public content and don't mind the whole
KB requiring login — but note the defaults assume the apps exist.

## 5. Verify (automated)

```bash
uv run kbtool verify-access
```

It probes the live site anonymously and asserts the behaviour matches your
`kb.yml`: private pages redirect to login, the public section and theme assets
are open, and the search index stays private. Exit 0 means the live Access
config matches the repo's record — a correctly-configured KB.

Next: [Using a KB](using-a-kb.md).
