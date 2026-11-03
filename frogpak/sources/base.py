"""The interface every forge adapter implements. Nothing outside sources/ may assume a forge."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class Asset:
    name: str
    url: str
    size: int | None = None
    # Changes when a file is replaced under the same name, which size alone can miss.
    id: int | str | None = None


@dataclass(frozen=True)
class Release:
    tag: str
    url: str
    assets: tuple


@dataclass(frozen=True)
class RepoInfo:
    url: str
    description: str


class SourceError(Exception):
    """A problem with one app's source; that app is skipped and the rest are published."""


def web_url(url, what):
    """Rejects anything but http(s): forge data ends up in links and downloads."""
    if not isinstance(url, str) or urlparse(url).scheme not in ("http", "https"):
        raise SourceError(f"{what} has an unusable address: {url!r}")
    return url


def one_line(text):
    return " ".join((text or "").split())


class Source(ABC):
    forge = ""
    web = ""

    @abstractmethod
    def info(self):
        """RepoInfo for the project's web page and description."""

    @abstractmethod
    def latest_release(self):
        """Newest non-pre-release Release, or None when there is none."""

    def download(self, asset, dest):
        """Fetches one asset to the path dest."""
        from .. import http
        http.download(asset.url, dest, self.headers())

    def headers(self):
        return {}
