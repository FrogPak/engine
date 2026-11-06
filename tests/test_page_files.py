import hashlib
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from frogpak import __version__, cli, config, fetch, http, images, log, theme

PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 32


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)

    def tearDown(self):
        self.dir.cleanup()

    def test_file_url_and_missing(self):
        (self.root / "logo.png").write_bytes(PNG)
        self.assertEqual(images.identity("logo.png", self.root), hashlib.sha256(PNG).hexdigest())
        self.assertEqual(images.identity("https://example.org/logo.svg", self.root), "https://example.org/logo.svg")
        self.assertIsNone(images.identity("missing.png", self.root))
        self.assertIsNone(images.identity(None, self.root))

    def test_paths_outside_the_pond_are_not_read(self):
        outside = self.root.parent / "outside-frogpak-test.png"
        outside.write_bytes(PNG)
        try:
            self.assertIsNone(images.identity("../outside-frogpak-test.png", self.root))
        finally:
            outside.unlink()

    def test_identities_include_the_default_logo(self):
        pond = config.parse("pond:\n  title: T\n  remote: t\n  css: style.css\napps:\n").pond
        (self.root / "logo.svg").write_bytes(b"<svg/>")
        (self.root / "style.css").write_text("a{}")
        found = images.identities(pond, self.root)
        self.assertEqual(found["logo"], hashlib.sha256(b"<svg/>").hexdigest())
        self.assertEqual(found["css"], hashlib.sha256(b"a{}").hexdigest())
        self.assertIsNone(found["favicon"])


class PollTests(unittest.TestCase):
    """Changing a file the page uses, with pond.yml unchanged, makes poll republish."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        (self.root / "pond.yml").write_text("pond:\n  title: T\n  remote: t\n  logo: assets/logo.png\napps:\n")
        (self.root / "assets").mkdir()
        (self.root / "assets/logo.png").write_bytes(PNG)
        self.cwd = Path.cwd()
        os.chdir(self.root)

    def tearDown(self):
        os.chdir(self.cwd)
        self.dir.cleanup()

    def published(self):
        cfg = config.load("pond.yml")
        return cli._normalize(fetch.fingerprint(cfg, [], __version__, None, images.identities(cfg.pond, ".")))

    def poll(self, state):
        out = io.StringIO()
        with mock.patch.object(http, "get_json", return_value={"state": state}), redirect_stdout(out):
            cli.main(["poll", "--base-url", "https://x.github.io/p"])
        return out.getvalue().strip()

    def test_unchanged(self):
        self.assertEqual(self.poll(self.published()), "changed=false")

    def test_new_logo_file(self):
        state = self.published()
        (self.root / "assets/logo.png").write_bytes(PNG + b"new")
        self.assertEqual(self.poll(state), "changed=true")


class ContrastTests(unittest.TestCase):
    def setUp(self):
        log.warnings.clear()

    def test_gnome_blue_passes(self):
        light, _ = theme.palettes({"accent": "1c71d8"})
        self.assertTrue(theme.readable("#1c71d8", light))
        self.assertEqual(log.warnings, [])

    def test_code_blocks_need_only_icon_contrast(self):
        palette = {"bg": "#ffffff", "card": "#ffffff", "code": "#d0d0d0"}
        # 4.5:1 or more on white, under 4.5:1 but over 3:1 on the gray: passes.
        self.assertGreater(theme.contrast("#1c71d8", "#d0d0d0"), theme.ICON_CONTRAST)
        self.assertLess(theme.contrast("#1c71d8", "#d0d0d0"), theme.TEXT_CONTRAST)
        self.assertTrue(theme.readable("#1c71d8", palette))

    def test_icon_warning(self):
        # Readable text on a white page, but a code-block color too close to the accent.
        light = theme.surfaces("#ffffff")
        light["code"] = "#6e9fe0"
        self.assertFalse(theme.readable("#1c71d8", light))

    def test_text_warning_still_applies(self):
        theme.palettes({"accent": "90dd40"})
        self.assertIn("text needs 4.5:1", log.warnings[0])


if __name__ == "__main__":
    unittest.main()
