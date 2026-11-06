import json
import tempfile
import unittest
from pathlib import Path

from frogpak import config, site

BASE = "pond:\n  title: T\n  remote: t\n"


def entry(app_id, name, released=None):
    return {"id": app_id, "name": name, "summary": "", "version": "1", "released": released, "license": None,
            "license_source": None, "url": "https://example.org", "icon": None, "links": {}, "arches": ["aarch64"]}


ENTRIES = [
    entry("net.dunevent.Sanctum", "Sanctum", "2026-11-02T01:35:31Z"),
    entry("io.github.nico359.loci", "loci", None),
    entry("net.dunevent.Barkeep", "Barkeep", "2026-11-02T03:50:14Z"),
    entry("io.github.FrogPak.Example", "FrogPak Example", "2026-11-05"),
    entry("io.github.nico359.camera", "Camera", None),
]


def names(order):
    return [e["name"] for e in site.ordered(ENTRIES, order)]


class OrderTests(unittest.TestCase):
    def test_listed_keeps_the_config_order(self):
        self.assertEqual(names("listed"), ["Sanctum", "loci", "Barkeep", "FrogPak Example", "Camera"])

    def test_name_ignores_case(self):
        self.assertEqual(names("name"), ["Barkeep", "Camera", "FrogPak Example", "loci", "Sanctum"])

    def test_newest_first_then_undated_by_name(self):
        # A date-only release counts as that day's start, so it still sorts after a later timestamp.
        self.assertEqual(names("newest"), ["FrogPak Example", "Barkeep", "Sanctum", "Camera", "loci"])

    def test_app_id_groups_authors(self):
        self.assertEqual(names("app-id"), ["FrogPak Example", "Camera", "loci", "Barkeep", "Sanctum"])

    def test_config(self):
        self.assertEqual(config.parse(BASE + "apps:\n").pond.order, "listed")
        for order in config.ORDERS:
            self.assertEqual(config.parse(BASE + f"  order: {order}\napps:\n").pond.order, order)
        with self.assertRaises(config.ConfigError) as ctx:
            config.parse(BASE + "  order: oldest\napps:\n")
        self.assertIn("pond.order must be one of listed, name, newest, app-id", ctx.exception.problems[0])

    def test_page_and_apps_json_follow_the_order(self):
        pond = config.parse(BASE + "  order: name\napps:\n").pond
        with tempfile.TemporaryDirectory() as out:
            site.write(Path(out), pond, "https://x/", "", ENTRIES, "logo.svg", None, False, {})
            page = (Path(out) / "index.html").read_text()
            listed = json.loads((Path(out) / "apps.json").read_text())["apps"]
        positions = [page.index(f"<h3>{n}") for n in ("Barkeep", "Camera", "FrogPak Example", "loci", "Sanctum")]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual([a["name"] for a in listed], ["Barkeep", "Camera", "FrogPak Example", "loci", "Sanctum"])


if __name__ == "__main__":
    unittest.main()
