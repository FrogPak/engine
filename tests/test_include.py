import tempfile
import unittest
from pathlib import Path

from frogpak import config, fetch, log

POND = """pond:
  title: T
  remote: t
include:
  - apps/alex.yml
  - apps/sam.yml
apps:
  org.example.First:
    repo: me/first
"""


class IncludeTests(unittest.TestCase):
    def setUp(self):
        log.warnings.clear()
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        (self.root / "apps").mkdir()
        (self.root / "pond.yml").write_text(POND)
        self.write("alex.yml", "apps:\n  org.example.Notes:\n    repo: alex/notes\n    license: MIT\n")
        self.write("sam.yml", "apps:\n  org.example.Paint:\n    repo: sam/paint\n")

    def tearDown(self):
        self.dir.cleanup()

    def write(self, name, text):
        (self.root / "apps" / name).write_text(text)

    def load(self):
        return config.load(self.root / "pond.yml")

    def test_apps_follow_pond_yml_in_include_order(self):
        cfg = self.load()
        self.assertEqual([a.id for a in cfg.apps], ["org.example.First", "org.example.Notes", "org.example.Paint"])
        self.assertEqual([a.source for a in cfg.apps], [None, "apps/alex.yml", "apps/sam.yml"])
        self.assertEqual(cfg.apps[1].license, "MIT")
        self.assertEqual(log.warnings, [])

    def test_first_listing_wins(self):
        self.write("sam.yml", "apps:\n  org.example.First:\n    repo: sam/first\n  org.example.Notes:\n    repo: x/y\n")
        cfg = self.load()
        self.assertEqual([(a.id, a.repo) for a in cfg.apps],
                         [("org.example.First", "me/first"), ("org.example.Notes", "alex/notes")])
        self.assertEqual(len(log.warnings), 2)
        self.assertIn("already listed in pond.yml", log.warnings[0])
        self.assertIn("already listed in apps/alex.yml", log.warnings[1])

    def test_missing_file_is_skipped_with_a_warning(self):
        (self.root / "apps" / "sam.yml").unlink()
        cfg = self.load()
        self.assertEqual([a.id for a in cfg.apps], ["org.example.First", "org.example.Notes"])
        self.assertIn("include apps/sam.yml: cannot be read", log.warnings[0])
        self.assertEqual(cfg.included[1], ("apps/sam.yml", None))

    def test_warn_false_is_quiet(self):
        (self.root / "apps" / "sam.yml").unlink()
        config.load(self.root / "pond.yml", warn=False)
        self.assertEqual(log.warnings, [])

    def test_mistakes_name_the_included_file(self):
        self.write("sam.yml", "pond:\n  title: X\napps:\n  org.example.Paint:\n    repo: sam/paint\n    color: red\n")
        with self.assertRaises(config.ConfigError) as caught:
            self.load()
        text = str(caught.exception)
        self.assertIn("apps/sam.yml", text)
        self.assertIn("unknown key pond", text)
        self.assertIn("apps.org.example.Paint.color", text)

    def test_paths_must_stay_in_the_repository(self):
        for bad in ("/etc/apps.yml", "../other/apps.yml", "apps/../../x.yml"):
            with self.assertRaises(config.ConfigError) as caught:
                config.parse(f"pond:\n  title: T\n  remote: t\ninclude: [{bad}]\n")
            self.assertIn("must be a path inside the repository", str(caught.exception))

    def test_include_must_be_a_list(self):
        with self.assertRaises(config.ConfigError) as caught:
            config.parse("pond:\n  title: T\n  remote: t\ninclude: apps/alex.yml\n")
        self.assertIn("include must be a list", str(caught.exception))

    def test_a_symlink_out_of_the_repository_is_not_read(self):
        outside = Path(self.dir.name).parent / "frogpak-outside-test.yml"
        outside.write_text("apps:\n  org.example.Secret:\n    repo: x/y\n")
        try:
            (self.root / "apps" / "sam.yml").unlink()
            (self.root / "apps" / "sam.yml").symlink_to(outside)
            cfg = self.load()
            self.assertNotIn("org.example.Secret", [a.id for a in cfg.apps])
            self.assertIn("outside the repository", log.warnings[0])
        finally:
            outside.unlink()

    def test_an_edited_include_changes_the_fingerprint(self):
        first = fetch.fingerprint(self.load(), [], "1")
        self.write("sam.yml", "apps:\n  org.example.Paint:\n    repo: sam/paint\n    assets: \"p-{arch}.flatpak\"\n")
        second = fetch.fingerprint(self.load(), [], "1")
        self.assertNotEqual(first["includes"], second["includes"])
        self.assertEqual(first["config"], second["config"])

    def test_no_include_needs_no_files(self):
        cfg = config.parse("pond:\n  title: T\n  remote: t\n")
        self.assertEqual((cfg.include, cfg.included), ((), ()))


if __name__ == "__main__":
    unittest.main()
