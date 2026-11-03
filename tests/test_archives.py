import tempfile
import unittest
import zipfile
from pathlib import Path

from frogpak import archives, log


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        log.warnings.clear()

    def tearDown(self):
        self.dir.cleanup()

    def make_zip(self, members):
        path = self.root / "release.zip"
        with zipfile.ZipFile(path, "w") as archive:
            for name, data in members.items():
                archive.writestr(name, data)
        return path

    def test_extracts_only_bundles_to_fixed_names(self):
        path = self.make_zip({"app-x86_64.flatpak": b"one", "nested/app-aarch64.FLATPAK": b"two",
                              "../../escape.flatpak": b"three", "README.md": b"x", "dir/": b""})
        out = self.root / "out"
        out.mkdir()
        found = archives.extract_bundles(path, out, "org.example.App-0")
        self.assertEqual([p.name for p in found],
                         ["org.example.App-0-0.flatpak", "org.example.App-0-1.flatpak", "org.example.App-0-2.flatpak"])
        self.assertEqual(sorted(p.read_bytes() for p in found), [b"one", b"three", b"two"])
        self.assertFalse((self.root / "escape.flatpak").exists())
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["out", "release.zip"])

    def test_size_limits(self):
        path = self.make_zip({"big.flatpak": b"x" * 5000, "small.flatpak": b"y" * 10})
        found = archives.extract_bundles(path, self.root, "a", max_member=1000)
        self.assertEqual([p.read_bytes() for p in found], [b"y" * 10])
        self.assertTrue(any("too large" in w for w in log.warnings))
        found = archives.extract_bundles(path, self.root, "b", max_total=100)
        self.assertEqual(found, [])

    def test_detection_and_bad_zips(self):
        bundle = self.root / "plain.flatpak"
        bundle.write_bytes(b"flatpak\0" + b"PK\x05\x06" * 10)
        self.assertFalse(archives.is_zip(bundle))
        self.assertTrue(archives.is_zip(self.make_zip({"a.flatpak": b"a"})))
        empty = self.make_zip({"notes.txt": b"x"})
        self.assertEqual(archives.extract_bundles(empty, self.root, "c"), [])
        self.assertTrue(any("no .flatpak bundle" in w for w in log.warnings))


if __name__ == "__main__":
    unittest.main()
