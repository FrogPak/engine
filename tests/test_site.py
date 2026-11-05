import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from frogpak import cli, config, repo, site

CONFIG = "pond:\n  title: T\n  remote: t\napps:\n"
METAINFO = b"""<?xml version="1.0"?>
<component type="desktop-application">
  <id>org.example.App</id>
  <metadata_license>CC0-1.0</metadata_license>
  <project_license>GPL-3.0-or-later</project_license>
  <name>Example</name>
  <url type="homepage">https://example.org/app</url>
  <url type="bugtracker">https://github.com/example/app/issues</url>
  <url type="donation">javascript:alert(1)</url>
  <url type="help">https://example.org/help</url>
  <summary>An example</summary>
  <releases>
    <release version="1.2.0" date="2026-11-03"/>
    <release version="1.1.0" date="2026-09-01"/>
  </releases>
</component>
"""


def entry(**changes):
    base = {"id": "org.example.App", "name": "Example", "summary": "An example", "version": "1.2.0",
            "released": "2026-11-03T18:04:00Z", "license": "GPL-3.0-or-later AND MIT",
            "license_source": "forge", "url": "https://github.com/example/app", "icon": None,
            "arches": ["aarch64"]}
    base.update(changes)
    return base


class PageTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.site = Path(self.dir.name)
        self.pond = config.parse(CONFIG).pond

    def tearDown(self):
        self.dir.cleanup()

    def write(self, entries, updated="2026-11-05T21:30:00Z"):
        site.write(self.site, self.pond, "https://x.github.io/t/", "", entries, "logo.svg", None, False,
                   {"state": 1}, updated=updated)
        return (self.site / "index.html").read_text()

    def test_updated_badge(self):
        page = self.write([])
        self.assertIn('<footer>Updated <time datetime="2026-11-05T21:30:00Z" data-format="datetime">'
                      "2026-11-05 21:30 UTC</time> · Published with", page)
        page = self.write([], updated=None)
        self.assertNotIn("Updated", page)
        self.assertIn("<footer>Published with", page)

    def test_card_facts(self):
        page = self.write([entry()])
        self.assertIn('Released <time datetime="2026-11-03T18:04:00Z" data-format="date">2026-11-03</time>', page)
        self.assertIn('<a href="https://spdx.org/licenses/GPL-3.0-or-later.html">GPL-3.0-or-later</a> AND '
                      '<a href="https://spdx.org/licenses/MIT.html">MIT</a>', page)

    def test_install_button_and_menu(self):
        page = self.write([entry()])
        self.assertIn('<a class="install-main" href="flatpak+https://x.github.io/t/org.example.App.flatpakref">',
                      page)
        menu = page[page.index('<div class="install-menu">'):page.index("</details>")]
        self.assertIn('<a href="org.example.App.flatpakref" download>Download .flatpakref</a>', menu)
        self.assertIn('flatpak install<span class="scope"></span> t org.example.App</code><button', menu)
        # The download moved into the menu; the card keeps only the Source link.
        self.assertEqual(page.count('org.example.App.flatpakref"'), 2)
        self.assertNotIn("Install file", page)

    def test_metainfo_links(self):
        links = {"homepage": "https://example.org/app", "bugtracker": "https://github.com/example/app/issues",
                 "donation": "https://example.org/donate"}
        row = self.links(self.write([entry(links=links)]))
        self.assertEqual([label for label in ("Source", "Website", "Issue tracker", "Donate") if label in row],
                         ["Source", "Website", "Issue tracker", "Donate"])
        self.assertIn('<a href="https://example.org/donate" rel="noopener">Donate</a>', row)

    def test_missing_links_are_left_off(self):
        row = self.links(self.write([entry(links={})]))
        self.assertIn("Source", row)
        for label in ("Website", "Issue tracker", "Donate"):
            self.assertNotIn(label, row)
        # A homepage that is the repository would repeat Source.
        row = self.links(self.write([entry(links={"homepage": "https://github.com/example/app/"})]))
        self.assertNotIn("Website", row)
        row = self.links(self.write([entry(links={"donation": "http://example.org/donate"})]))
        self.assertNotIn("Donate", row)

    def links(self, page):
        start = page.index('<div class="links">')
        return page[start:page.index("</div>", start)]

    def test_copy_buttons_have_names(self):
        page = self.write([entry()])
        self.assertEqual(page.count('<span class="visually-hidden">Copy</span></button>'), 2)
        self.assertNotIn('<button type="button">Copy</button>', page)

    def test_missing_facts(self):
        page = self.write([entry(released=None, license=None)])
        self.assertNotIn("Released", page)
        self.assertIn("License not stated", page)

    def test_license_text_is_escaped(self):
        page = self.write([entry(license='"><script>x</script>')])
        self.assertNotIn("<script>x", page)

    def test_apps_json(self):
        self.write([entry()])
        data = json.loads((self.site / site.STATE_FILE).read_text())
        self.assertEqual(data["updated"], "2026-11-05T21:30:00Z")
        self.assertEqual(data["apps"][0]["license"], "GPL-3.0-or-later AND MIT")
        self.assertEqual(data["apps"][0]["released"], "2026-11-03T18:04:00Z")
        # The publish time stays out of the state poll compares, or every check would republish.
        self.assertEqual(data["state"], {"state": 1})


class MetadataTests(unittest.TestCase):
    def test_license_and_release_date(self):
        def cat(_repo, _ref, path):
            return METAINFO if path.endswith(".metainfo.xml") else None
        with mock.patch.object(repo, "_cat", side_effect=cat):
            meta = repo.read_metadata("r", "app/org.example.App/aarch64/stable", "org.example.App")
        self.assertEqual((meta.license, meta.released, meta.version), ("GPL-3.0-or-later", "2026-11-03", "1.2.0"))
        # Only the shown types, and only https: the donation link here is not.
        self.assertEqual(meta.links, {"homepage": "https://example.org/app",
                                      "bugtracker": "https://github.com/example/app/issues"})


class NowTests(unittest.TestCase):
    def test_source_date_epoch(self):
        with mock.patch.dict("os.environ", {"SOURCE_DATE_EPOCH": "1762378200"}):
            self.assertEqual(cli._now(), "2025-11-05T21:30:00Z")


if __name__ == "__main__":
    unittest.main()
