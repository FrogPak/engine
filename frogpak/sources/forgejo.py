"""Forgejo and Gitea, including Codeberg. Both serve the same /api/v1 release API."""
from .. import http
from .base import Asset, Release, RepoInfo, Source, SourceError, iso_time, one_line, web_url


class Forgejo(Source):
    forge = "forgejo"

    def __init__(self, base_url, owner_repo):
        self.owner_repo = owner_repo
        self.api = f"{base_url.rstrip('/')}/api/v1/repos/{owner_repo}"
        self.web = f"{base_url.rstrip('/')}/{owner_repo}"

    def _get(self, path):
        try:
            return http.get_json(self.api + path, {"Accept": "application/json"})
        except http.HTTPError as error:
            if error.status == 404:
                return None
            raise SourceError(f"{self.owner_repo}: {error}") from None

    def info(self):
        data = self._get("")
        if data is None:
            raise SourceError(f"{self.owner_repo}: repository not found or not public")
        # Newer Gitea versions list the licenses they detect; older ones and Forgejo may not.
        # Several files do not say whether both apply or either does, so only one is used.
        found = data.get("licenses")
        license = one_line(found[0]) if isinstance(found, list) and len(found) == 1 \
            and isinstance(found[0], str) else ""
        return RepoInfo(url=web_url(data.get("html_url"), self.owner_repo),
                        description=one_line(data.get("description")), license=license or None)

    def latest_release(self):
        # /releases/latest skips drafts and pre-releases.
        data = self._get("/releases/latest")
        if data is None:
            return None
        assets = tuple(Asset(a["name"], web_url(a.get("browser_download_url"), a["name"]), a.get("size"), a.get("id"))
                       for a in data.get("assets", []))
        return Release(tag=data["tag_name"], url=web_url(data.get("html_url"), data["tag_name"]), assets=assets,
                       published=iso_time(data.get("published_at")))
