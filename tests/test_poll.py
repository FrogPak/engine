import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from frogpak import __version__, cli, fetch, http, images
from frogpak.sources import Asset, Release

CONFIG = """pond:
  title: T
  remote: t
apps:
  org.example.App:
    repo: example/app
"""


class FakeSource:
    def __init__(self, tag):
        self.tag = tag

    def latest_release(self):
        return Release(self.tag, "u", (Asset("org.example.App-x86_64.flatpak", "u", 5),
                                       Asset("org.example.App-aarch64.flatpak", "u", 6)))


class PollTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.config = Path(self.dir.name) / "frogpak.yml"
        self.config.write_text(CONFIG)

    def tearDown(self):
        self.dir.cleanup()

    def poll(self, tag, published):
        def get_json(url, headers=None):
            if isinstance(published, Exception):
                raise published
            return {"state": published}
        out = io.StringIO()
        with mock.patch("frogpak.sources.resolve", return_value=FakeSource(tag)), \
                mock.patch.object(http, "get_json", side_effect=get_json), redirect_stdout(out):
            cli.main(["poll", "--config", str(self.config), "--base-url", "https://x.github.io/pond"])
        return out.getvalue().strip()

    def state(self, tag):
        from frogpak import config
        cfg = config.load(self.config)
        with mock.patch("frogpak.sources.resolve", return_value=FakeSource(tag)):
            # As publish records it, including the files the page is built from.
            return cli._normalize(fetch.fingerprint(cfg, fetch.survey(cfg), __version__, None,
                                                    images.identities(cfg.pond, ".")))

    def test_unchanged(self):
        self.assertEqual(self.poll("v1", self.state("v1")), "changed=false")

    def test_new_release(self):
        self.assertEqual(self.poll("v2", self.state("v1")), "changed=true")

    def test_config_change(self):
        published = self.state("v1")
        self.config.write_text(CONFIG.replace("title: T", "title: T2"))
        self.assertEqual(self.poll("v1", published), "changed=true")

    def test_first_publish(self):
        self.assertEqual(self.poll("v1", http.HTTPError("u", 404)), "changed=true")


if __name__ == "__main__":
    unittest.main()
