import os

from .. import http
from .base import Asset, Release, RepoInfo, Source, SourceError, one_line, web_url

API = "https://api.github.com"


class GitHub(Source):
    forge = "github"

    def __init__(self, owner_repo):
        self.owner_repo = owner_repo
        self.web = f"https://github.com/{owner_repo}"

    def headers(self):
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        # Unauthenticated calls are limited to 60 an hour.
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _get(self, path):
        try:
            return http.get_json(f"{API}/repos/{self.owner_repo}{path}", self.headers())
        except http.HTTPError as error:
            if error.status == 404:
                return None
            raise SourceError(f"{self.owner_repo}: {error}") from None

    def info(self):
        data = self._get("")
        if data is None:
            raise SourceError(f"{self.owner_repo}: repository not found or not public")
        return RepoInfo(url=web_url(data.get("html_url"), self.owner_repo),
                        description=one_line(data.get("description")))

    def latest_release(self):
        # /releases/latest skips drafts and pre-releases.
        data = self._get("/releases/latest")
        if data is None:
            return None
        assets = tuple(Asset(a["name"], web_url(a.get("browser_download_url"), a["name"]), a.get("size"), a.get("id"))
                       for a in data.get("assets", []))
        return Release(tag=data["tag_name"], url=web_url(data.get("html_url"), data["tag_name"]), assets=assets)

    def download(self, asset, dest):
        # Public assets need no token, and urllib would forward the Authorization header
        # through the redirect to the storage host.
        http.download(asset.url, dest)
