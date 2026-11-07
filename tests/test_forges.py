import tempfile
import unittest
from pathlib import Path

from frogpak import config, forges, site


class ForgeIconTests(unittest.TestCase):
    def test_icon_follows_the_host_then_the_forge(self):
        cases = [
            ("https://github.com/alex/notes", "github", "github"),
            ("https://codeberg.org/alex/notes", "forgejo", "codeberg"),
            ("https://git.example.org/alex/notes", "forgejo", "forgejo"),
            ("https://gitea.com/alex/notes", "gitea", "gitea"),
            ("https://git.example.org/alex/notes", "gitea", "gitea"),
            ("https://gitlab.com/alex/notes", "gitlab", "gitlab"),
            ("https://example.org/notes", None, "code"),
        ]
        for url, forge, expected in cases:
            self.assertEqual(forges.icon_name(url, forge), expected, url)

    def test_every_icon_takes_the_link_color(self):
        for name in forges.PATHS:
            self.assertIn('fill="currentColor"', forges.mark("https://example.org/", name))

    def test_cards_use_their_forge_icon(self):
        p = config.parse("pond:\n  title: T\n  remote: t\napps:\n").pond
        entry = {"id": "org.example.App", "name": "App", "summary": "", "version": "1", "released": None,
                 "license": None, "url": "https://codeberg.org/alex/app", "forge": "forgejo", "icon": None,
                 "arches": ["x86_64"]}
        with tempfile.TemporaryDirectory() as out:
            site.write(out, p, "https://x.github.io/t/", "https://github.com/x/t", [entry], "logo.svg", None,
                       False, {})
            page = (Path(out) / "index.html").read_text()
        card = page.split('id="org.example.App"')[1]
        self.assertIn(forges.PATHS["codeberg"], card)
        self.assertNotIn(forges.PATHS["github"], card)
        header = page.split('id="org.example.App"')[0]
        self.assertIn(forges.PATHS["github"], header)


if __name__ == "__main__":
    unittest.main()
