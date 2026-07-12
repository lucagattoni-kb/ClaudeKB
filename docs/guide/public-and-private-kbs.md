# Public vs private KBs

A KB has **two independent visibility axes**. Confusing them is the single
biggest source of accidental exposure, so this page separates them clearly.

| Axis | Controlled by | Exposes | Default |
|---|---|---|---|
| **Repo visibility** | GitHub (repo setting) | Markdown **source**, full **git history**, commit author emails | private |
| **Site visibility** | Cloudflare Access (`kb.yml: visibility`) | The **rendered** content to anonymous web visitors | private (login required) |

They are set in different places and mean different things. A KB can be any
combination of the two.

## The four combinations

| Repo | Site | What it means | Use when |
|---|---|---|---|
| private | private | Fully private (the default). Only you (and your agents) see source or content. | Personal/internal knowledge. |
| private | **public** | The **rendered content is world-readable**, but drafts, history, source, and commit metadata stay private. | You want to publish polished content but keep the "workshop" (history, unpublished pages) private. **The common way to publish a KB.** |
| **public** | private | Source is world-readable (so the content is public *anyway*, via the repo), but the live site still asks for login. The Access gate adds essentially **no confidentiality**. | Rarely useful — usually a mistake. Only if you want the repo open for collaboration but a separate "official" gated site. |
| **public** | **public** | Everything is open: source, history, and the live site. | Open knowledge you're happy to have fully in the open, contributions welcome. |

**Key insight:** *repo public* and *site public* are different exposures.
Making the **site** public (`kb.yml: visibility: public`) publishes the
rendered content but keeps your git history and source private. Making the
**repo** public exposes everything the site does **plus** all source and all
history — including content you later deleted and the email on every commit.

## What "site public" exposes

Setting `kb.yml: visibility: public` (and skipping the Access apps) makes the
deployed site world-readable:

- All **published** pages, the **search index** (`search.json`), and the
  sitemap become public. (These are exactly the public content — expected.)
- Unpublished drafts still only exist in the repo, not the site, so they stay
  private **as long as the repo is private**.
- Mixed model: a *private* site can still expose a `docs/public/` subsection —
  see [Using a KB](using-a-kb.md). Note its two documented limits: the global
  nav leaks private page **titles**, and public pages can't show private
  **raster images**.

## What "repo public" exposes (and the risks)

Making the GitHub repo public is a bigger step. Before you do it:

1. **History is forever.** Every past commit is cloneable — including content
   you since deleted and the **author email** on each commit. Vet the whole
   history, not just the current tree. If a personal email or removed secret
   is in history, rewrite it first (`git filter-repo`) or start a fresh repo.
2. **Commit identity.** KBs written by agents commit with whatever git identity
   is configured. Set the repo to use your **GitHub noreply** email so history
   is publish-safe by default (the scaffold playbook does this — see
   [Create a KB](create-a-kb.md)).
3. **Secrets in content.** A credential written into a public KB is a live
   leak. `kbtool check` scans content for likely secrets (keys, tokens,
   private-key blocks) and **fails the gate on a public KB** if it finds one
   (see the guardrail below).
4. **Cross-KB links leak structure.** A public KB containing
   `kb://private-kb/topic.md` reveals the **existence and paths** of your
   private KBs (the link is in the HTML even though it redirects to login).
   Don't reference private KBs from public ones if their existence is sensitive.
5. **Reduced obscurity, not reduced security.** A public KB (or the public
   blueprint) reveals the `kb-<name>.<domain>` hostname pattern. Protection is
   authentication, not secrecy, so this is fine — expect that someone could
   enumerate your KB hostnames and hit login walls.

## The guardrail: secret scanning

`kbtool check` scans `docs/**/*.md` for likely secrets on every run:

- **Public KB** (`visibility: public`): a high-confidence match (private-key
  block, AWS/GitHub/Google/Slack token, `key = <long-value>`) is an **error** —
  it fails `check` and the deploy gate, so the secret never ships.
- **Private KB**: the same match is a **warning** — you learn about it *before*
  you ever flip the KB public.
- Personal emails and generic `secret = …` assignments are always warnings
  (they're often intentional). Example domains (`example.com`), `git@…`, and
  noreply addresses are ignored.
- **Intentional example?** Put `kbtool-allow-secret` anywhere on the line
  (e.g. a trailing comment) to suppress the finding for that line.

## Checklist: making a KB public

1. Decide **which axis** you actually want (usually: site public, repo your
   choice).
2. Site public → set `kb.yml: visibility: public`, skip/remove the Access apps,
   re-run `uv run kbtool verify-access` (it now expects `/` to be open).
3. Repo public → **PRIMARY CHECK the history**: personal emails, secrets,
   deleted sensitive content. Rewrite history if needed. Confirm the commit
   identity is your noreply.
4. Run `uv run kbtool check` — a clean run on a public KB means no detectable
   secrets ship.
5. Confirm no `kb://` links to private KBs you don't want disclosed.
