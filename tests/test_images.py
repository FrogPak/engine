import tempfile
import unittest
from pathlib import Path

from frogpak import config, images, log

SVG_WIDE = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 100"><rect width="300" height="100"/></svg>'
SVG_SIZED = b'<?xml version="1.0"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="64px" height="48"></svg>'


def png(width, height):
    import struct
    return b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + struct.pack(">II", width, height) + b"\x08\x06\x00\x00\x00"


def pond(**kwargs):
    return config.Pond(title="T", remote="t", **kwargs)


class ImageTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.pond_dir = Path(self.dir.name)
        log.warnings.clear()

    def tearDown(self):
        self.dir.cleanup()

    def test_sniff_and_size(self):
        self.assertEqual(images.sniff(SVG_WIDE), "svg")
        self.assertEqual(images.sniff(png(10, 20)), "png")
        self.assertIsNone(images.sniff(b"GIF89a"))
        self.assertEqual(images.size(images.Image(SVG_WIDE, "svg", "x")), (300.0, 100.0))
        self.assertEqual(images.size(images.Image(SVG_SIZED, "svg", "x")), (64.0, 48.0))
        self.assertEqual(images.size(images.Image(png(10, 20), "png", "x")), (10, 20))

    def test_default_logo_without_files(self):
        logo, dark, favicon = images.resolve(pond(), self.pond_dir)
        self.assertEqual(logo.origin, "FrogPak default logo")
        self.assertIsNone(dark)
        self.assertIs(favicon, logo)

    def test_default_file_names_prefer_svg(self):
        (self.pond_dir / "logo.png").write_bytes(png(64, 64))
        (self.pond_dir / "logo.svg").write_bytes(SVG_SIZED)
        (self.pond_dir / "logo-dark.png").write_bytes(png(64, 64))
        logo, dark, _ = images.resolve(pond(), self.pond_dir)
        self.assertEqual((logo.origin, dark.origin), ("logo.svg", "logo-dark.png"))

    def test_wide_logo_warns_about_favicon(self):
        (self.pond_dir / "logo.svg").write_bytes(SVG_WIDE)
        images.resolve(pond(), self.pond_dir)
        self.assertTrue(any("not square" in w for w in log.warnings))
        log.warnings.clear()
        (self.pond_dir / "icon.png").write_bytes(png(32, 32))
        images.resolve(pond(favicon="icon.png"), self.pond_dir)
        self.assertFalse(log.warnings)

    def test_paths_must_stay_in_repo(self):
        logo, _, _ = images.resolve(pond(logo="../outside.svg"), self.pond_dir)
        self.assertEqual(logo.origin, "FrogPak default logo")
        self.assertTrue(any("inside the pond repository" in w for w in log.warnings))

    def test_unreadable_or_wrong_type_falls_back(self):
        (self.pond_dir / "logo.gif").write_bytes(b"GIF89a....")
        logo, _, _ = images.resolve(pond(logo="logo.gif"), self.pond_dir)
        self.assertEqual(logo.origin, "FrogPak default logo")
        logo, _, _ = images.resolve(pond(logo="missing.svg"), self.pond_dir)
        self.assertEqual(logo.origin, "FrogPak default logo")


if __name__ == "__main__":
    unittest.main()
