import io
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

from frogpak import cli, config, log

MINIMAL = "pond:\n  title: T\n  remote: t\napps:\n"


class FindTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        log.warnings.clear()

    def tearDown(self):
        self.dir.cleanup()

    def write(self, name):
        (self.root / name).write_text(MINIMAL)

    def test_pond_yml(self):
        self.write("pond.yml")
        self.assertEqual(config.find(root=self.root), self.root / "pond.yml")
        self.assertEqual(log.warnings, [])

    def test_old_name_still_works_with_a_warning(self):
        self.write("frogpak.yml")
        self.assertEqual(config.find(root=self.root), self.root / "frogpak.yml")
        self.assertIn("rename it to pond.yml", log.warnings[0])

    def test_both_uses_pond_yml_and_warns(self):
        self.write("pond.yml")
        self.write("frogpak.yml")
        self.assertEqual(config.find(root=self.root), self.root / "pond.yml")
        self.assertIn("frogpak.yml is ignored", log.warnings[0])

    def test_neither_names_pond_yml(self):
        with self.assertRaises(config.ConfigError) as ctx:
            config.load(config.find(root=self.root))
        self.assertEqual(Path(ctx.exception.path).name, "pond.yml")

    def test_explicit_path_is_used_as_given(self):
        self.write("pond.yml")
        self.assertEqual(config.find("custom.yml", self.root), Path("custom.yml"))
        self.assertEqual(log.warnings, [])

    def test_warn_false_is_quiet(self):
        self.write("frogpak.yml")
        self.assertEqual(config.find(root=self.root, warn=False), self.root / "frogpak.yml")
        self.assertEqual(log.warnings, [])


class CheckCommandTests(unittest.TestCase):
    """The workflow runs check with no --config unless a Pond sets one."""

    def run_check(self, names):
        with tempfile.TemporaryDirectory() as root:
            for name in names:
                (Path(root) / name).write_text(MINIMAL)
            log.warnings.clear()
            cwd = Path.cwd()
            try:
                import os
                os.chdir(root)
                out = io.StringIO()
                # FrogPak logs to stderr.
                with redirect_stderr(out):
                    code = cli.main(["check"])
            finally:
                os.chdir(cwd)
            return code, out.getvalue(), list(log.warnings)

    def test_check_finds_pond_yml(self):
        code, out, warnings = self.run_check(["pond.yml"])
        self.assertEqual(code, 0)
        self.assertIn("pond.yml: OK", out)
        self.assertEqual(warnings, [])

    def test_check_falls_back_to_frogpak_yml(self):
        code, out, warnings = self.run_check(["frogpak.yml"])
        self.assertEqual(code, 0)
        self.assertIn("frogpak.yml: OK", out)
        self.assertEqual(len(warnings), 1)


if __name__ == "__main__":
    unittest.main()
