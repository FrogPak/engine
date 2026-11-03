import unittest

from frogpak import config, log, theme

BASE = "pond:\n  title: T\n  remote: t\n  theme:\n{}apps:\n"


class ThemeConfigTests(unittest.TestCase):
    def parse(self, lines):
        return config.parse(BASE.format(lines))

    def problems(self, lines):
        with self.assertRaises(config.ConfigError) as ctx:
            self.parse(lines)
        return ctx.exception.problems

    def test_valid_colors(self):
        cfg = self.parse('    accent: "#26A269"\n    background: "#fff"\n')
        self.assertEqual(cfg.pond.theme, {"accent": "#26a269", "background": "#fff"})

    def test_unquoted_color_is_a_comment(self):
        found = self.problems("    accent: #26a269\n")
        self.assertIn("drop the #", found[0])

    def test_forms_without_hash(self):
        cfg = self.parse("    accent: 26a269\n    accent-dark: 012345\n    background: 000000\n"
                         '    background-dark: "#ABC"\n')
        self.assertEqual(cfg.pond.theme, {"accent": "#26a269", "accent-dark": "#012345",
                                          "background": "#000000", "background-dark": "#abc"})

    def test_bad_values_and_keys(self):
        found = self.problems('    accent: "green"\n    text: "#000"\n')
        joined = "\n".join(found)
        self.assertIn("must be a hex color", joined)
        self.assertIn("unknown key pond.theme.text", joined)


class PaletteTests(unittest.TestCase):
    def setUp(self):
        log.warnings.clear()

    def test_no_theme_keeps_defaults_without_warnings(self):
        light, dark = theme.palettes({})
        self.assertEqual(light["accent"], theme.LIGHT["accent"])
        self.assertEqual(dark["accent"], theme.DARK["accent"])
        self.assertEqual(log.warnings, [])

    def test_derived_dark_accent_is_readable(self):
        _, dark = theme.palettes({"accent": "#1a5fb4"})
        self.assertGreaterEqual(theme.worst_contrast(dark["accent"], dark), theme.TEXT_CONTRAST)

    def test_explicit_low_contrast_accent_is_kept_and_warned(self):
        light, _ = theme.palettes({"accent": "#26a269"})
        self.assertEqual(light["accent"], "#26a269")
        self.assertTrue(any("pond.theme.accent" in w and "would pass" in w for w in log.warnings))

    def test_custom_background_gets_readable_text(self):
        light, dark = theme.palettes({"background": "#002b36"})
        self.assertGreaterEqual(theme.contrast(light["fg"], light["bg"]), 7)
        self.assertGreaterEqual(theme.worst_contrast(light["accent"], light), theme.TEXT_CONTRAST)
        self.assertNotEqual(dark["bg"], theme.DARK["bg"])

    def test_text_on_accent(self):
        self.assertEqual(theme.readable_on("#1c71d8"), "#ffffff")
        self.assertEqual(theme.readable_on("#f8e45c"), theme.INK)


if __name__ == "__main__":
    unittest.main()
