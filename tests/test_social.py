import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from frogpak import config, fetch, http, log, site, social

PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 32
JPEG = b"\xff\xd8\xff\xe0" + b"\0" * 32
SVG = b'<svg xmlns="http://www.w3.org/2000/svg"/>'
UPLOADED = "https://repository-images.githubusercontent.com/123/abc"
ACTIONS = {"GITHUB_REPOSITORY": "FuriHub/repo", "GITHUB_TOKEN": "t"}


def pond(text=""):
    return config.parse("pond:\n  title: FuriHub\n  subtitle: Apps <for> phones\n  remote: f\n" + text + "apps:\n").pond


def reply(url=UPLOADED, custom=True):
    return {"data": {"repository": {"openGraphImageUrl": url, "usesCustomOpenGraphImage": custom}}}


class RepositoryImageTests(unittest.TestCase):
    def setUp(self):
        log.warnings.clear()

    def test_uploaded_image(self):
        with mock.patch.dict("os.environ", ACTIONS), mock.patch.object(http, "post_json", return_value=reply()) as post:
            self.assertEqual(social.repository_image(), UPLOADED)
        url, payload, headers = post.call_args[0]
        self.assertEqual(url, "https://api.github.com/graphql")
        self.assertEqual(payload["variables"], {"owner": "FuriHub", "name": "repo"})
        self.assertEqual(headers, {"Authorization": "Bearer t"})

    def test_generated_card_is_not_used(self):
        generated = reply("https://opengraph.githubassets.com/1/FuriHub/repo", custom=False)
        with mock.patch.dict("os.environ", ACTIONS), mock.patch.object(http, "post_json", return_value=generated):
            self.assertIsNone(social.repository_image())

    def test_outside_actions_asks_nothing(self):
        with mock.patch.dict("os.environ", {}, clear=True), mock.patch.object(http, "post_json") as post:
            self.assertIsNone(social.repository_image())
        post.assert_not_called()

    def test_lookup_failure_warns_unless_quiet(self):
        failing = mock.patch.object(http, "post_json", side_effect=http.HTTPError("u", 403))
        with mock.patch.dict("os.environ", ACTIONS), failing:
            self.assertIsNone(social.repository_image(warn=False))
            self.assertEqual(log.warnings, [])
            self.assertIsNone(social.repository_image())
        self.assertIn("social preview image", log.warnings[0])

    def test_unexpected_reply(self):
        for odd in ({}, {"data": None}, {"errors": [{"message": "x"}]}, reply("http://insecure", True)):
            with mock.patch.dict("os.environ", ACTIONS), mock.patch.object(http, "post_json", return_value=odd):
                self.assertIsNone(social.repository_image())

    def test_setting_wins_without_asking_github(self):
        with mock.patch.dict("os.environ", ACTIONS), mock.patch.object(http, "post_json") as post:
            self.assertEqual(social.source(pond("  social-image: assets/social.png\n")), "assets/social.png")
        post.assert_not_called()


class FileTests(unittest.TestCase):
    def setUp(self):
        log.warnings.clear()
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        self.site = self.root / "site"
        self.site.mkdir()

    def tearDown(self):
        self.dir.cleanup()

    def test_png_and_jpeg_are_copied(self):
        for data, name in ((PNG, "social.png"), (JPEG, "social.jpg")):
            (self.root / "image").write_bytes(data)
            self.assertEqual(social.write(self.site, "image", self.root), name)
            self.assertEqual((self.site / name).read_bytes(), data)

    def test_uploaded_image_is_downloaded(self):
        with mock.patch.object(http, "get_bytes", return_value=PNG) as get:
            self.assertEqual(social.write(self.site, UPLOADED, self.root), "social.png")
        self.assertEqual(get.call_args[0][0], UPLOADED)

    def test_other_files_fall_back_to_the_icon(self):
        (self.root / "image.svg").write_bytes(SVG)
        self.assertIsNone(social.write(self.site, "image.svg", self.root))
        self.assertIn("not a PNG or JPEG", log.warnings[-1])
        self.assertIsNone(social.write(self.site, "http://example.org/a.png", self.root))
        self.assertIsNone(social.write(self.site, "missing.png", self.root))
        self.assertIsNone(social.write(self.site, None, self.root))

    def test_identity(self):
        (self.root / "image").write_bytes(PNG)
        self.assertEqual(social.identity("image", self.root), hashlib.sha256(PNG).hexdigest())
        self.assertEqual(social.identity(UPLOADED, self.root), UPLOADED)
        self.assertIsNone(social.identity(None, self.root))
        self.assertIsNone(social.identity("missing.png", self.root))


class TagTests(unittest.TestCase):
    def test_with_an_image(self):
        tags = site.social_tags(pond(), "https://furihub.github.io/repo/", "social.png")
        self.assertIn('<meta property="og:image" content="https://furihub.github.io/repo/social.png">', tags)
        self.assertIn('<meta name="twitter:card" content="summary_large_image">', tags)
        self.assertIn('<meta property="og:url" content="https://furihub.github.io/repo/">', tags)
        self.assertIn('<meta property="og:description" content="Apps &lt;for&gt; phones">', tags)

    def test_without_an_image_the_icon_is_offered(self):
        tags = site.social_tags(pond(), "https://x.github.io/p/", None)
        self.assertIn('<meta property="og:image" content="https://x.github.io/p/icon-256.png">', tags)
        self.assertIn('<meta name="twitter:card" content="summary">', tags)

    def test_no_subtitle_no_description(self):
        plain = config.parse("pond:\n  title: T\n  remote: t\napps:\n").pond
        self.assertNotIn("description", site.social_tags(plain, "https://x/", None))


class ChangeTests(unittest.TestCase):
    def test_a_new_image_changes_the_fingerprint(self):
        cfg = config.parse("pond:\n  title: T\n  remote: t\napps:\n")
        first = fetch.fingerprint(cfg, [], "1", UPLOADED)
        self.assertNotEqual(first, fetch.fingerprint(cfg, [], "1", UPLOADED + "2"))
        self.assertEqual(first, fetch.fingerprint(cfg, [], "1", UPLOADED))


if __name__ == "__main__":
    unittest.main()
