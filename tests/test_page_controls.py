import tempfile
import unittest
from pathlib import Path

from frogpak import config, site


def entry(app_id, arches, version="1.0"):
    return {"id": app_id, "name": app_id.rsplit(".", 1)[1], "summary": "", "version": version, "released": None,
            "license": None, "license_source": None, "url": "https://github.com/a/b", "icon": None, "links": {},
            "arches": arches}


def page(pond_yaml="", entries=None, dark=None):
    cfg = config.parse("pond:\n  title: T\n  remote: t\n" + pond_yaml)
    with tempfile.TemporaryDirectory() as out:
        site.write(out, cfg.pond, "https://example.org/", None,
                   entries if entries is not None else [entry("org.example.A", ["x86_64", "aarch64"])],
                   "logo.svg", dark, False, {})
        return Path(out, "index.html").read_text()


class ModeTests(unittest.TestCase):
    def test_default_is_system(self):
        self.assertEqual(config.parse("pond:\n  title: T\n  remote: t\n").pond.mode, "system")
        html = page()
        self.assertIn('<html lang="en">', html)
        self.assertIn('data-mode-choice="system" aria-pressed="true"', html)

    def test_mode_setting(self):
        cfg = config.parse("pond:\n  title: T\n  remote: t\n  theme:\n    mode: dark\n    accent: 1966c2\n")
        self.assertEqual(cfg.pond.mode, "dark")
        self.assertEqual(cfg.pond.theme, {"accent": "#1966c2"})
        html = page("  theme:\n    mode: dark\n")
        self.assertIn('<html lang="en" data-mode="dark">', html)
        self.assertIn('data-mode-choice="dark" aria-pressed="true"', html)

    def test_bad_mode(self):
        with self.assertRaises(config.ConfigError) as caught:
            config.parse("pond:\n  title: T\n  remote: t\n  theme:\n    mode: auto\n")
        self.assertIn("pond.theme.mode must be one of system, light, dark", str(caught.exception))

    def test_dark_logo_follows_the_toggle(self):
        html = page(dark="logo-dark.svg")
        self.assertNotIn("<picture>", html)
        self.assertIn('<img class="logo-light" src="logo.svg"', html)
        self.assertIn('<img class="logo-dark" src="logo-dark.svg"', html)
        self.assertIn('<img src="logo.svg" alt="">', page())


class ArchPickerTests(unittest.TestCase):
    def test_picker_lists_the_ponds_arches(self):
        html = page(entries=[entry("org.example.A", ["aarch64", "x86_64"]), entry("org.example.B", ["x86_64"])])
        self.assertIn('data-arch="" aria-pressed="true">All<', html)
        self.assertLess(html.index('data-arch="x86_64"'), html.index('data-arch="aarch64"'))
        self.assertIn('data-arches="aarch64 x86_64"', html)
        self.assertIn('data-arches="x86_64"', html)

    def test_no_picker_for_one_arch_or_no_apps(self):
        self.assertNotIn('data-arch=""', page("  arches: [aarch64]\n", [entry("org.example.A", ["aarch64"])]))
        self.assertNotIn('data-arch=""', page(entries=[]))

    def test_version_is_kept_whole(self):
        self.assertIn("A <small>1.0</small>", page())


if __name__ == "__main__":
    unittest.main()
