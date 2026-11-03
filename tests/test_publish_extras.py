import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from frogpak import cli, config, log


class SizeGuardTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.out = Path(self.dir.name)
        (self.out / "objects").mkdir()
        (self.out / "objects" / "big").write_bytes(b"x" * 900)
        self.bundle = self.out / "b.flatpak"
        self.bundle.write_bytes(b"x" * 100)
        self.bundles = [(SimpleNamespace(app=SimpleNamespace(id="org.example.App")), "x86_64", self.bundle)]
        log.warnings.clear()

    def tearDown(self):
        self.dir.cleanup()

    def test_under_limit_passes(self):
        with mock.patch.object(cli, "PAGES_LIMIT", 10_000):
            self.assertTrue(cli.size_guard(self.out, self.bundles))
        self.assertEqual(log.warnings, [])

    def test_near_limit_warns(self):
        with mock.patch.object(cli, "PAGES_LIMIT", 1200):
            self.assertTrue(cli.size_guard(self.out, self.bundles))
        self.assertIn("org.example.App", log.warnings[0])

    def test_over_limit_fails(self):
        with mock.patch.object(cli, "PAGES_LIMIT", 900):
            self.assertFalse(cli.size_guard(self.out, self.bundles))


class CssConfigTests(unittest.TestCase):
    def test_css_key(self):
        cfg = config.parse("pond:\n  title: T\n  remote: t\n  css: style/custom.css\napps:\n")
        self.assertEqual(cfg.pond.css, "style/custom.css")


if __name__ == "__main__":
    unittest.main()
