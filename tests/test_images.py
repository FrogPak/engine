import tempfile
import unittest
from unittest import mock
from pathlib import Path

from frogpak import config, images, log

SVG_WIDE = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 100"><rect width="300" height="100"/></svg>'
SVG_SQUARE = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><rect width="128" height="128"/></svg>'
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
        logos = images.resolve(pond(), self.pond_dir)
        self.assertEqual(logos.header.origin, "FrogPak default logo")
        self.assertIsNone(logos.header_dark)
        self.assertFalse(logos.wide)
        self.assertIs(logos.favicon, logos.header)
        self.assertIs(logos.badge, logos.header)
        self.assertIs(logos.badge_dark, logos.header)

    def test_square_and_wide(self):
        for name, data in (("square.svg", SVG_SQUARE), ("square-dark.svg", SVG_SQUARE), ("wide.svg", SVG_WIDE),
                           ("wide-dark.svg", SVG_WIDE)):
            (self.pond_dir / name).write_bytes(data)
        logos = images.resolve(pond(logo_square="square.svg", logo_square_dark="square-dark.svg",
                                    logo_wide="wide.svg", logo_wide_dark="wide-dark.svg"), self.pond_dir)
        self.assertTrue(logos.wide)
        self.assertEqual((logos.header.origin, logos.header_dark.origin), ("wide.svg", "wide-dark.svg"))
        self.assertEqual((logos.favicon.origin, logos.badge.origin, logos.badge_dark.origin),
                         ("square.svg", "square.svg", "square-dark.svg"))
        self.assertFalse(log.warnings)

    def test_square_only_works_as_logo_did(self):
        (self.pond_dir / "square.svg").write_bytes(SVG_SQUARE)
        logos = images.resolve(pond(logo_square="square.svg"), self.pond_dir)
        self.assertFalse(logos.wide)
        self.assertEqual({logos.header.origin, logos.favicon.origin, logos.badge.origin, logos.badge_dark.origin},
                         {"square.svg"})

    def test_wide_only_warns_and_shrinks_the_wide_logo(self):
        (self.pond_dir / "wide.svg").write_bytes(SVG_WIDE)
        (self.pond_dir / "wide-dark.svg").write_bytes(SVG_WIDE)
        logos = images.resolve(pond(logo_wide="wide.svg", logo_wide_dark="wide-dark.svg"), self.pond_dir)
        self.assertTrue(any("logo-square is not set" in w for w in log.warnings))
        self.assertEqual((logos.favicon.origin, logos.badge.origin, logos.badge_dark.origin),
                         ("wide.svg", "wide.svg", "wide-dark.svg"))

    def test_favicon_overrides_only_the_favicon(self):
        (self.pond_dir / "square.svg").write_bytes(SVG_SQUARE)
        (self.pond_dir / "icon.png").write_bytes(png(32, 32))
        logos = images.resolve(pond(logo_square="square.svg", favicon="icon.png"), self.pond_dir)
        self.assertEqual((logos.favicon.origin, logos.icon.origin, logos.badge.origin),
                         ("icon.png", "square.svg", "square.svg"))

    def test_favicon_override_leaves_the_remote_icon_alone(self):
        square = images.Image(SVG_SQUARE.replace(b"/>", b' fill="#ff0000"/>'), "svg", "square")
        favicon = images.Image(SVG_SQUARE.replace(b"/>", b' fill="#0000ff"/>'), "svg", "favicon")
        site = self.pond_dir / "site"
        site.mkdir()
        images.write_icons(favicon, square, site)

        def rendered(image, side):
            path = self.pond_dir / f"expected-{side}.png"
            images.render_png(images._square_svg(image, side), path, side, side)
            return path.read_bytes()
        self.assertEqual((site / images.FAVICON).read_bytes(), rendered(favicon, 32))
        self.assertEqual((site / images.TOUCH_ICON).read_bytes(), rendered(favicon, 180))
        self.assertEqual((site / images.ICON).read_bytes(), rendered(square, 256))
        self.assertEqual((site / "favicon.svg").read_bytes(), favicon.data)

    def test_square_logo_that_is_not_square_warns(self):
        (self.pond_dir / "square.svg").write_bytes(SVG_WIDE)
        images.resolve(pond(logo_square="square.svg"), self.pond_dir)
        self.assertTrue(any("not square" in w for w in log.warnings))

    def test_deprecated_logo_stands_in_for_logo_square_with_a_notice(self):
        (self.pond_dir / "old.svg").write_bytes(SVG_SQUARE)
        (self.pond_dir / "old-dark.svg").write_bytes(SVG_SQUARE)
        with mock.patch.object(log, "notice") as notice:
            logos = images.resolve(pond(logo="old.svg", logo_dark="old-dark.svg"), self.pond_dir)
        self.assertEqual((logos.header.origin, logos.header_dark.origin), ("old.svg", "old-dark.svg"))
        self.assertEqual(len([c for c in notice.call_args_list if "deprecated" in c.args[0]]), 2)
        self.assertFalse(log.warnings)

    def test_default_file_names(self):
        (self.pond_dir / "logo.png").write_bytes(png(64, 64))
        (self.pond_dir / "logo.svg").write_bytes(SVG_SIZED)
        (self.pond_dir / "logo-dark.png").write_bytes(png(64, 64))
        logos = images.resolve(pond(), self.pond_dir)
        self.assertEqual((logos.header.origin, logos.header_dark.origin), ("logo.svg", "logo-dark.png"))
        (self.pond_dir / "logo-square.svg").write_bytes(SVG_SQUARE)
        (self.pond_dir / "logo-wide.png").write_bytes(png(300, 100))
        logos = images.resolve(pond(), self.pond_dir)
        self.assertEqual((logos.header.origin, logos.badge.origin), ("logo-wide.png", "logo-square.svg"))

    def test_paths_must_stay_in_repo(self):
        logos = images.resolve(pond(logo_square="../outside.svg"), self.pond_dir)
        self.assertEqual(logos.header.origin, "FrogPak default logo")
        self.assertTrue(any("inside the Pond repository" in w for w in log.warnings))

    def test_unreadable_or_wrong_type_falls_back(self):
        (self.pond_dir / "logo.gif").write_bytes(b"GIF89a....")
        self.assertEqual(images.resolve(pond(logo_square="logo.gif"), self.pond_dir).header.origin,
                         "FrogPak default logo")
        self.assertEqual(images.resolve(pond(logo_square="missing.svg"), self.pond_dir).header.origin,
                         "FrogPak default logo")


if __name__ == "__main__":
    unittest.main()
