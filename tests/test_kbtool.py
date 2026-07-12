"""Unit tests for kbtool's pure logic (fast; the e2e harness covers integration)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from kbtool import links, nav, preprocess, secrets, verify  # noqa: E402


def _write(tmp_path, name, body):
    p = tmp_path / "docs" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")


def test_secrets_high_confidence_errors_on_public(tmp_path):
    _write(tmp_path, "p.md", "token: ghp_" + "a" * 36 + "\n")
    pub = secrets.scan(tmp_path, is_public=True)
    priv = secrets.scan(tmp_path, is_public=False)
    assert any(lvl == "error" for lvl, *_ in pub)      # error on public KB
    assert priv and all(lvl == "warning" for lvl, *_ in priv)  # warning on private KB


def test_secrets_private_key_block(tmp_path):
    _write(tmp_path, "k.md", "```\n-----BEGIN OPENSSH PRIVATE KEY-----\nabc\n```\n")
    assert any("private key" in msg for _, msg, *_ in secrets.scan(tmp_path, is_public=True))


def test_secrets_personal_email_is_warning(tmp_path):
    _write(tmp_path, "e.md", "Contact someone@gmail.com for access.\n")
    found = secrets.scan(tmp_path, is_public=True)
    assert found and all(lvl == "warning" for lvl, *_ in found)


def test_secrets_ignores_example_and_git_emails(tmp_path):
    _write(tmp_path, "ok.md", "See you@example.com and `git@github.com:o/r.git`.\n")
    assert secrets.scan(tmp_path, is_public=True) == []


def test_secrets_allow_marker_suppresses(tmp_path):
    _write(tmp_path, "a.md", "token: ghp_" + "a" * 36 + "  <!-- kbtool-allow-secret -->\n")
    assert secrets.scan(tmp_path, is_public=True) == []


def test_secrets_clean_content(tmp_path):
    _write(tmp_path, "c.md", "# Title\n\nOrdinary prose with no credentials.\n")
    assert secrets.scan(tmp_path, is_public=True) == []


def test_derive_probes_private_with_bypasses():
    kb = {
        "visibility": "private",
        "platform": {"access_apps": [
            {"name": "kb-x", "policy": "allow-owner"},
            {"name": "kb-x-public", "policy": "bypass-everyone", "path": "/public"},
            {"name": "kb-x-assets", "policy": "bypass-everyone", "path": "/assets"},
        ]},
    }
    probes = verify.derive_probes(kb)
    by_path = {p.path: p.expect for p in probes}
    assert by_path["/"] == "gated"
    assert by_path["/search.json"] == "gated"
    assert by_path["/public/"] == "open"
    assert by_path[verify.ASSET_TOKEN] == "open"


def test_derive_probes_public_kb():
    probes = verify.derive_probes({"visibility": "public"})
    assert probes == [verify.Probe("/", "open", "visibility: public")]


@pytest.mark.parametrize("status,headers,expected", [
    (200, {}, "open"),
    (302, {"Location": "https://team.cloudflareaccess.com/cdn-cgi/access/login/x"}, "gated"),
    (302, {"Location": "https://elsewhere.example/"}, "other:302"),
    (403, {}, "gated"),
    (404, {}, "other:404"),
])
def test_classify(status, headers, expected):
    assert verify.classify(status, headers) == expected


@pytest.mark.parametrize("text,expected", [
    # normal link: only the URL is rewritten
    ("[Alpha](/concepts/alpha.md)", "[Alpha](/concepts/alpha/)"),
    # link text equals the URL string — must not corrupt the text (R2 regression)
    ("[/concepts/alpha.md](/concepts/alpha.md)", "[/concepts/alpha.md](/concepts/alpha/)"),
    # cross-KB rewrite
    ("[x](kb://other/p.md)", "[x](https://kb-other.example.com/p/)"),
    # non-.md asset link left untouched
    ("![a](/media/x.png)", "![a](/media/x.png)"),
])
def test_rewrite_links(text, expected):
    assert preprocess._rewrite_links(text, "sandbox", "example.com") == expected


@pytest.mark.parametrize("src,url", [
    ("/concepts/alpha.md", "/concepts/alpha/"),
    ("concepts/alpha.md", "/concepts/alpha/"),
    ("/index.md", "/"),
    ("/concepts/index.md", "/concepts/"),
    ("/assets/x/diagram.png", "/assets/x/diagram.png"),
])
def test_source_path_to_url_path(src, url):
    assert links.source_path_to_url_path(src) == url


def test_cross_kb_url():
    assert links.cross_kb_url("other", "concepts/x.md", "example.com") == \
        "https://kb-other.example.com/concepts/x/"


@pytest.mark.parametrize("target,ok", [
    ("kb://other-kb/a/b.md", True),
    ("kb://Bad/a.md", False),      # uppercase slug
    ("kb://x/", False),            # empty path is invalid
    ("notkb://x/a", False),
])
def test_parse_kb_link(target, ok):
    assert (links.parse_kb_link(target) is not None) == ok


def test_find_links_and_external():
    text = "[a](/x.md) ![i](/p.png) [e](https://h/x) [f](#frag) [k](kb://o/p.md)"
    got = {l.target for l in links.find_links(text)}
    assert got == {"/x.md", "/p.png", "https://h/x", "#frag", "kb://o/p.md"}
    assert links.is_external("https://h/x")
    assert not links.is_external("kb://o/p.md")
    assert links.is_anchor_only("#frag")


@pytest.mark.parametrize("pattern,path,match", [
    ("public/**.md", "public/a.md", True),
    ("public/**.md", "public/sub/a.md", True),
    ("public/**.md", "other/a.md", False),
    ("concepts/*.md", "concepts/a.md", True),
    ("concepts/*.md", "concepts/sub/a.md", False),
])
def test_glob_to_regex(pattern, path, match):
    assert bool(nav.glob_to_regex(pattern).match(path)) == match


def test_nav_coverage_and_expand(tmp_path):
    docs = tmp_path / "docs"
    (docs / "concepts").mkdir(parents=True)
    (docs / "index.md").write_text("# Home")
    (docs / "concepts" / "beta.md").write_text(
        "---\ntitle: Beta\ntype: concept\ndescription: d\n---\n# Beta\n"
    )
    (docs / "concepts" / "alpha.md").write_text(
        "---\ntitle: Alpha\ntype: concept\ndescription: d\n---\n# Alpha\n"
    )
    navspec = [{"Home": "index.md"}, {"Concepts": {"glob": "concepts/**.md"}}]
    covered = nav.covered_paths(navspec, docs)
    assert covered == {"index.md", "concepts/alpha.md", "concepts/beta.md"}
    expanded = nav.expand(navspec, docs)
    # glob section sorted by title: Alpha before Beta
    concepts = expanded[1]["Concepts"]
    assert [list(e.values())[0] for e in concepts] == ["concepts/alpha.md", "concepts/beta.md"]
