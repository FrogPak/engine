import unittest

from frogpak import config, licenses, log

MINIMAL = """
pond:
  title: T
  remote: t
apps:
  org.example.App:
    repo: example/app
"""


class ResolveTests(unittest.TestCase):
    def setUp(self):
        log.warnings.clear()

    def resolve(self, value, forge, meta):
        return licenses.resolve("org.example.App", value, forge, meta)

    def test_auto_prefers_the_forge(self):
        self.assertEqual(self.resolve("auto", "MIT", "MIT"), ("MIT", "forge"))
        self.assertEqual(self.resolve("auto", None, "MIT"), ("MIT", "meta"))
        self.assertEqual(self.resolve("auto", None, None), (None, None))
        self.assertEqual(log.warnings, [])

    def test_forge_cannot_tell(self):
        for unknown in ("NOASSERTION", "Other", "", "  "):
            self.assertEqual(self.resolve("auto", unknown, "MIT"), ("MIT", "meta"))

    def test_disagreement_warns_and_forge_wins(self):
        self.assertEqual(self.resolve("auto", "GPL-3.0", "MIT"), ("GPL-3.0", "forge"))
        self.assertIn("license: meta", log.warnings[0])

    def test_same_license_more_precisely_from_metainfo(self):
        self.assertEqual(self.resolve("auto", "GPL-3.0", "GPL-3.0-or-later"), ("GPL-3.0-or-later", "meta"))
        self.assertEqual(self.resolve("auto", "GPL-3.0-only", "GPL-3.0-or-later"), ("GPL-3.0-only", "forge"))
        self.assertEqual(len(log.warnings), 1)

    def test_forge_or_meta_only(self):
        self.assertEqual(self.resolve("forge", "GPL-3.0", "MIT"), ("GPL-3.0", "forge"))
        self.assertEqual(self.resolve("meta", "GPL-3.0", "MIT"), ("MIT", "meta"))
        self.assertEqual(log.warnings, [])
        self.assertEqual(self.resolve("meta", "MIT", None), (None, None))
        self.assertIn("states no license", log.warnings[0])

    def test_configured_license_is_the_last_fallback(self):
        self.assertEqual(self.resolve("Apache-2.0", None, None), ("Apache-2.0", "config"))
        self.assertEqual(self.resolve("MIT", "MIT", None), ("MIT", "forge"))
        self.assertEqual(log.warnings, [])
        self.assertEqual(self.resolve("Apache-2.0", None, "MIT"), ("MIT", "meta"))
        self.assertIn("differs from MIT from the metainfo", log.warnings[0])


class EquivalentTests(unittest.TestCase):
    def test_gnu_spellings(self):
        self.assertTrue(licenses.equivalent("GPL-2.0+", "GPL-2.0-or-later"))
        self.assertTrue(licenses.equivalent("gpl-3.0", "GPL-3.0-only"))
        self.assertTrue(licenses.equivalent("LGPL-2.1", "LGPL-2.1-or-later"))
        self.assertTrue(licenses.equivalent("AGPL-3", "AGPL-3.0-only"))
        self.assertFalse(licenses.equivalent("GPL-3.0-only", "GPL-3.0-or-later"))
        self.assertFalse(licenses.equivalent("GPL-2.0", "GPL-3.0"))

    def test_expressions(self):
        self.assertTrue(licenses.equivalent("GPL-3.0-or-later AND MIT", "gpl-3.0+ and mit"))
        self.assertFalse(licenses.equivalent("MIT", "MIT OR Apache-2.0"))


class PartsTests(unittest.TestCase):
    def test_ids_are_linked_and_operators_are_not(self):
        self.assertEqual(licenses.parts("(MIT OR Apache-2.0)"), [
            ("(", None), ("MIT", "https://spdx.org/licenses/MIT.html"), ("OR", None),
            ("Apache-2.0", "https://spdx.org/licenses/Apache-2.0.html"), (")", None)])

    def test_license_refs(self):
        self.assertEqual(licenses.parts("LicenseRef-proprietary=https://example.org/eula"),
                         [("LicenseRef-proprietary", "https://example.org/eula")])
        self.assertEqual(licenses.parts("LicenseRef-x=javascript:alert(1)")[0], ("LicenseRef-x", None))
        self.assertEqual(licenses.parts("<b>"), [("<b>", None)])


class ConfigTests(unittest.TestCase):
    def test_default_and_keywords(self):
        self.assertEqual(config.parse(MINIMAL).apps[0].license, "auto")
        for value, mode in (("repo", "forge"), ("Forge", "forge"), ("metainfo", "meta"), ("meta", "meta")):
            self.assertEqual(config.parse(MINIMAL + f"    license: {value}\n").apps[0].license, mode)

    def test_expression(self):
        cfg = config.parse(MINIMAL + '    license: "GPL-3.0-or-later AND MIT"\n')
        self.assertEqual(cfg.apps[0].license, "GPL-3.0-or-later AND MIT")

    def test_bad_values(self):
        for value in ('"<script>"', "yes", '"x\\ny"'):
            with self.assertRaises(config.ConfigError) as ctx:
                config.parse(MINIMAL + f"    license: {value}\n")
            self.assertIn("license", ctx.exception.problems[0])


if __name__ == "__main__":
    unittest.main()
