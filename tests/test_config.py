import unittest

from frogpak import config

MINIMAL = """
pond:
  title: Test Pond
  remote: testpond
apps:
  org.example.App:
    repo: example/app
"""


class ConfigTests(unittest.TestCase):
    def problems(self, text):
        with self.assertRaises(config.ConfigError) as ctx:
            config.parse(text)
        return ctx.exception.problems

    def test_minimal_gets_defaults(self):
        cfg = config.parse(MINIMAL)
        self.assertEqual(cfg.pond.title, "Test Pond")
        self.assertEqual(cfg.pond.arches, ("x86_64", "aarch64"))
        app = cfg.apps[0]
        self.assertEqual((app.id, app.repo, app.assets, app.name),
                         ("org.example.App", "example/app", config.DEFAULT_ASSETS, "App"))

    def test_problems_are_reported_together(self):
        found = self.problems("pond:\n  titel: x\napps:\n  bad:\n    repo: a/b\n")
        joined = "\n".join(found)
        self.assertIn("unknown key pond.titel", joined)
        self.assertIn("pond.title is required", joined)
        self.assertIn("pond.remote is required", joined)
        self.assertIn("not a valid Flatpak app ID", joined)

    def test_duplicate_keys_rejected(self):
        found = self.problems(MINIMAL + "  org.example.App:\n    repo: other/app\n")
        self.assertIn("duplicate key", found[0])

    def test_yaml_type_guessing_rejected(self):
        found = self.problems(MINIMAL.replace("remote: testpond", "remote: no"))
        self.assertIn("must be text", found[0])
        self.assertIn("quotes", found[0])

    def test_remote_name_rules(self):
        found = self.problems(MINIMAL.replace("remote: testpond", "remote: Test_Pond"))
        self.assertIn("lowercase", found[0])

    def test_app_id_rules(self):
        self.assertTrue(config.valid_app_id("org.example.My-App"))
        self.assertFalse(config.valid_app_id("org.my-example.App"))
        self.assertFalse(config.valid_app_id("example.App"))
        self.assertFalse(config.valid_app_id("org.example.1App"))

    def test_asset_pattern_placeholders(self):
        cfg = config.parse(MINIMAL + '    assets: "{name}.flatpak"\n')
        self.assertEqual(cfg.apps[0].assets, "{name}.flatpak")
        found = self.problems(MINIMAL + '    assets: "{version}-{arch}.flatpak"\n')
        self.assertIn("placeholders", found[0])
        found = self.problems(MINIMAL + '    assets: "dir/{arch}.flatpak"\n')
        self.assertIn("cannot contain '/'", found[0])

    def test_repo_forms(self):
        cfg = config.parse(MINIMAL.replace("example/app", "https://codeberg.org/example/app"))
        self.assertEqual(cfg.apps[0].repo, "https://codeberg.org/example/app")
        found = self.problems(MINIMAL.replace("example/app", "example"))
        self.assertIn("owner/repo", found[0])

    def test_forge_values(self):
        found = self.problems(MINIMAL + "    forge: sourcehut\n")
        self.assertIn("forge must be one of", found[0])

    def test_empty_apps_allowed(self):
        cfg = config.parse("pond:\n  title: T\n  remote: t\napps:\n")
        self.assertEqual(cfg.apps, ())


if __name__ == "__main__":
    unittest.main()
