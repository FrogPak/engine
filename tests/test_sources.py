import json
import unittest
from pathlib import Path
from unittest import mock

from frogpak import config, fetch, http, sources
from frogpak.sources import Asset, Release
from frogpak.sources.forgejo import Forgejo
from frogpak.sources.github import GitHub

FIXTURES = Path(__file__).parent / "fixtures"


def app(assets=config.DEFAULT_ASSETS):
    return config.App("org.example.App", "example/app", assets)


class ResolveTests(unittest.TestCase):
    def test_owner_repo_and_github_url(self):
        self.assertEqual(sources.resolve("example/app").owner_repo, "example/app")
        self.assertEqual(sources.resolve("https://github.com/example/app.git").owner_repo, "example/app")

    def test_forgejo_and_gitea_urls(self):
        source = sources.resolve("https://codeberg.org/example/app")
        self.assertIsInstance(source, Forgejo)
        self.assertEqual(source.api, "https://codeberg.org/api/v1/repos/example/app")
        source = sources.resolve("https://example.org:3000/git/example/app.git", "gitea")
        self.assertEqual(source.api, "https://example.org:3000/git/api/v1/repos/example/app")
        with self.assertRaisesRegex(sources.SourceError, "owner/repo"):
            sources.resolve("https://codeberg.org/example")

    def test_gitlab_not_yet_supported(self):
        with self.assertRaisesRegex(sources.SourceError, "gitlab is not supported yet"):
            sources.resolve("https://git.example.org/a/b", "gitlab")

    def test_unknown_host_needs_forge(self):
        with self.assertRaisesRegex(sources.SourceError, "set 'forge:'"):
            sources.resolve("https://git.example.org/a/b")


class GitHubTests(unittest.TestCase):
    def test_latest_release(self):
        data = json.loads((FIXTURES / "github-release.json").read_text())
        with mock.patch.object(http, "get_json", return_value=data) as get:
            release = GitHub("example/app").latest_release()
        self.assertTrue(get.call_args[0][0].endswith("/repos/example/app/releases/latest"))
        self.assertEqual(release.tag, "v1.2.0")
        self.assertEqual([a.name for a in release.assets],
                         ["org.example.App-aarch64.flatpak", "org.example.App-x86_64.flatpak", "notes.txt"])

    def test_no_release_is_none(self):
        error = http.HTTPError("u", 404)
        with mock.patch.object(http, "get_json", side_effect=error):
            self.assertIsNone(GitHub("example/app").latest_release())

    def test_other_http_errors_become_source_errors(self):
        with mock.patch.object(http, "get_json", side_effect=http.HTTPError("u", 403)):
            with self.assertRaises(sources.SourceError):
                GitHub("example/app").info()


class ForgejoTests(unittest.TestCase):
    def test_latest_release(self):
        data = json.loads((FIXTURES / "forgejo-release.json").read_text())
        with mock.patch.object(http, "get_json", return_value=data) as get:
            release = Forgejo("https://codeberg.org", "example/app").latest_release()
        self.assertEqual(get.call_args[0][0], "https://codeberg.org/api/v1/repos/example/app/releases/latest")
        self.assertEqual(release.tag, "v1.2.0")
        found = fetch.match_assets(app(), release, ("x86_64", "aarch64"))
        self.assertEqual(sorted(arch for arch, _ in found), ["aarch64", "x86_64"])

    def test_missing_release_and_errors(self):
        source = Forgejo("https://codeberg.org", "example/app")
        with mock.patch.object(http, "get_json", side_effect=http.HTTPError("u", 404)):
            self.assertIsNone(source.latest_release())
            with self.assertRaisesRegex(sources.SourceError, "not found"):
                source.info()
        with mock.patch.object(http, "get_json", side_effect=http.HTTPError("u", 500)):
            with self.assertRaises(sources.SourceError):
                source.latest_release()


class SafetyTests(unittest.TestCase):
    def test_only_web_addresses(self):
        from frogpak.sources import base
        self.assertEqual(base.web_url("https://a.org/x", "x"), "https://a.org/x")
        for bad in ("file:///etc/passwd", "javascript:alert(1)", None):
            with self.assertRaises(sources.SourceError):
                base.web_url(bad, "x")
        self.assertEqual(base.one_line("two\nlines  here"), "two lines here")

    def test_page_links_and_log_escaping(self):
        import io
        from contextlib import redirect_stderr
        from frogpak import log, site
        self.assertEqual(site._web("javascript:alert(1)"), "#")
        out = io.StringIO()
        with mock.patch.object(log, "_ACTIONS", True), redirect_stderr(out):
            log.notice("a\nb %")
        self.assertEqual(out.getvalue().strip(), "::notice::a%0Ab %25")


class MatchTests(unittest.TestCase):
    release = Release("v1", "u", (
        Asset("org.example.App-x86_64.flatpak", "u1", 10),
        Asset("org.example.App-aarch64.flatpak", "u2", 20),
        Asset("App-x86_64-latest.flatpak", "u3", 30),
        Asset("App-x86_64-v1.flatpak", "u4", 40),
    ))

    def test_default_pattern(self):
        found = fetch.match_assets(app(), self.release, ("x86_64", "aarch64"))
        self.assertEqual([(arch, a.url) for arch, a in found], [("x86_64", "u1"), ("aarch64", "u2")])

    def test_custom_pattern_and_missing_arch(self):
        found = fetch.match_assets(app("{name}-{arch}-latest.flatpak"), self.release, ("x86_64", "aarch64"))
        self.assertEqual([(arch, a.url) for arch, a in found], [("x86_64", "u3")])

    def test_ambiguous_pattern_skips_arch(self):
        found = fetch.match_assets(app("{name}-{arch}-*.flatpak"), self.release, ("x86_64",))
        self.assertEqual(found, [])

    def test_pattern_without_arch_takes_every_match(self):
        found = fetch.match_assets(app("App-*.flatpak"), self.release, ("x86_64", "aarch64"))
        self.assertEqual([(arch, a.url) for arch, a in found], [(None, "u3"), (None, "u4")])


if __name__ == "__main__":
    unittest.main()
