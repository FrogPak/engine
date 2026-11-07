import dataclasses
import json
import shutil
import tempfile
import unittest
import xml.dom.minidom
from pathlib import Path

from frogpak import badges, config, images, theme


def pond(title="Alex's Apps", theme_colors=None):
    return config.Pond(title=title, remote="alex", subtitle="", arches=("x86_64",), logo=None, logo_dark=None,
                       favicon=None, theme=theme_colors or {}, css=None)


class BadgeTests(unittest.TestCase):
    def test_wider_text_makes_wider_badges(self):
        short = badges.version_badge("A", "v1", "#1c71d8", "t")
        long = badges.version_badge("A much longer Pond name", "v1.10.200", "#1c71d8", "t")
        width = lambda svg: int(svg.split('width="')[1].split('"')[0])
        self.assertGreater(width(long), width(short))

    def test_text_is_escaped_and_valid_xml(self):
        svg = badges.version_badge('<Tom & "Jerry">', "v1", "#1c71d8", 'Tom & "Jerry", published with FrogPak')
        xml.dom.minidom.parseString(svg)
        self.assertNotIn("<Tom", svg)

    def test_value_text_reads_on_accent(self):
        light = badges.version_badge("P", "v1", "#f6d32d", "t")
        self.assertIn(f'fill="{theme.INK}">v1', light)
        dark = badges.version_badge("P", "v1", "#1c71d8", "t")
        self.assertIn(f'fill="{theme.WHITE}">v1', dark)

    @unittest.skipUnless(shutil.which("rsvg-convert"), "needs rsvg-convert")
    def test_write_makes_buttons_and_one_badge_per_app(self):
        logo = images.Image((images.DATA / "default-logo.svg").read_bytes(), "svg", "default")
        entries = [{"id": "org.example.Notes", "version": "1.2.0"}, {"id": "org.example.Paint", "version": ""}]
        with tempfile.TemporaryDirectory() as site:
            made = badges.write(site, pond(), entries, logo, logo)
            names = made.versions
            self.assertEqual(names, {"org.example.Notes": "badges/org.example.Notes.svg",
                                     "org.example.Paint": "badges/org.example.Paint.svg"})
            for name in ["badges/button-light.svg", "badges/button-dark.svg", *names.values()]:
                text = (Path(site) / name).read_text()
                xml.dom.minidom.parseString(text)
                self.assertIn("<title>Alex's Apps, published with FrogPak</title>", text)
            self.assertIn(">available<", (Path(site) / names["org.example.Paint"]).read_text())
            self.assertEqual(sorted(p.name for p in (Path(site) / "badges").iterdir()),
                             ["button-dark.svg", "button-light.svg", "org.example.Notes.svg", "org.example.Paint.svg"])

    @unittest.skipUnless(shutil.which("rsvg-convert"), "needs rsvg-convert")
    def test_version_badges_use_the_accent_of_the_starting_appearance(self):
        logo = images.Image((images.DATA / "default-logo.svg").read_bytes(), "svg", "default")
        entries = [{"id": "org.example.Notes", "version": "1.0"}]
        colors = {"accent": "#1a5f2a", "accent-dark": "#a6e22e"}
        for mode, expected in (("light", "#1a5f2a"), ("system", "#1a5f2a"), ("dark", "#a6e22e")):
            p = dataclasses.replace(pond(theme_colors=colors), mode=mode)
            with tempfile.TemporaryDirectory() as site:
                made = badges.write(site, p, entries, logo, logo)
                svg = (Path(site) / made.versions["org.example.Notes"]).read_text()
            self.assertIn(f'fill="{expected}"', svg, mode)

    def test_snippets_link_to_the_pond_or_the_app_and_escape_alt_text(self):
        p = pond('My [Best] "Apps"')
        button_html, button_md = badges.button_snippets(p, "https://alex.github.io/p/")
        self.assertIn('<a href="https://alex.github.io/p/">', button_html)
        self.assertIn('alt="My [Best] &quot;Apps&quot;, published with FrogPak"', button_html)
        self.assertEqual(button_md, '[![My \\[Best\\] "Apps", published with FrogPak]'
                                    "(https://alex.github.io/p/badges/button-light.svg)](https://alex.github.io/p/)")
        badge = badges.badge_snippet(p, "https://alex.github.io/p/", "org.example.Notes", "badges/org.example.Notes.svg")
        self.assertTrue(badge.startswith('[![My \\[Best\\] "Apps", published with FrogPak]'))
        self.assertTrue(badge.endswith("(https://alex.github.io/p/#org.example.Notes)"))


class PageBadgeTests(unittest.TestCase):
    def publish(self, made, url="https://codeberg.org/example/app", order="listed"):
        from frogpak import site
        p = config.parse(f"pond:\n  title: T\n  remote: t\n  order: {order}\napps:\n").pond
        entries = [
            {"id": "org.example.Zed", "name": "Zed", "summary": "", "version": "2.0", "released": None,
             "license": None, "url": url, "icon": None, "arches": ["x86_64"]},
            {"id": "org.example.App", "name": "Example", "summary": "", "version": "1.2.0", "released": None,
             "license": None, "url": url, "icon": None, "arches": ["x86_64"]},
        ]
        with tempfile.TemporaryDirectory() as out:
            (Path(out) / "badges").mkdir()
            site.write(out, p, "https://x.github.io/t/", "", entries, "logo.svg", None, False, {}, made_badges=made)
            page = (Path(out) / "index.html").read_text()
            badge_page = (Path(out) / "badges" / "index.html")
            badge_page = badge_page.read_text() if badge_page.exists() else None
            data = json.loads((Path(out) / "apps.json").read_text())
        return page, badge_page, data

    MADE = badges.Made(200, {"org.example.App": "badges/org.example.App.svg",
                             "org.example.Zed": "badges/org.example.Zed.svg"})

    def test_cards_have_anchors_but_no_badges(self):
        page, _, _ = self.publish(self.MADE)
        self.assertIn('<div class="card app" id="org.example.App"', page)
        self.assertNotIn("badges/", page)

    def test_badges_page_has_the_button_once_then_each_app_in_order(self):
        _, listed, _ = self.publish(self.MADE)
        self.assertEqual(listed.count('src="button-light.svg"'), 1)
        self.assertIn("[![T, published with FrogPak](https://x.github.io/t/badges/org.example.App.svg)]"
                      "(https://x.github.io/t/#org.example.App)", listed)
        self.assertLess(listed.index("<h3>Zed</h3>"), listed.index("<h3>Example</h3>"))
        _, by_name, _ = self.publish(self.MADE, order="name")
        self.assertLess(by_name.index("<h3>Example</h3>"), by_name.index("<h3>Zed</h3>"))

    def test_apps_json_lists_the_badges(self):
        _, _, data = self.publish(self.MADE)
        self.assertEqual(data["badges"]["page"], "https://x.github.io/t/badges/")
        self.assertEqual({a["id"]: a["badge"] for a in data["apps"]}["org.example.App"],
                         "https://x.github.io/t/badges/org.example.App.svg")

    def test_no_badges_page_without_badges(self):
        _, badge_page, data = self.publish(None)
        self.assertIsNone(badge_page)
        self.assertNotIn("badges", data)

    def test_install_command_has_a_copy_button_for_any_forge(self):
        # The copy button once depended on the app's source being on GitHub.
        page, _, _ = self.publish(None)
        menu = page.split('<div class="install-menu">')[1].split("</details>")[0]
        self.assertIn('<button type="button">', menu)


if __name__ == "__main__":
    unittest.main()
