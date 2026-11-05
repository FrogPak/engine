"""The interface every forge adapter implements. Nothing outside sources/ may assume a forge."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime, timezone
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
    # When the release was published, as from iso_time; None when the forge does not say.
    published: str | None = None


@dataclass(frozen=True)
class RepoInfo:
    url: str
    description: str
    # The license the forge detected, as an SPDX expression; None when it cannot tell.
    license: str | None = None


class SourceError(Exception):
    """A problem with one app's source; that app is skipped and the rest are published."""


def web_url(url, what):
    """Rejects anything but http(s): forge data ends up in links and downloads."""
    if not isinstance(url, str) or urlparse(url).scheme not in ("http", "https"):
        raise SourceError(f"{what} has an unusable address: {url!r}")
    return url


def one_line(text):
    return " ".join((text or "").split())


def iso_time(value):
    """A timestamp as 2026-11-03T18:04:00Z, or a date as 2026-11-03; None if unreadable.

    Accepts ISO 8601 text and Unix timestamps, as forges and AppStream write them.
    """
    try:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            moment = datetime.fromtimestamp(value, timezone.utc)
        elif isinstance(value, str) and value.strip():
            text = value.strip()
            if text.isdigit():
                moment = datetime.fromtimestamp(int(text), timezone.utc)
            elif len(text) == 10:
                return date.fromisoformat(text).isoformat()
            else:
                # Python 3.10 does not read a trailing Z.
                moment = datetime.fromisoformat(text.replace("Z", "+00:00").replace("z", "+00:00"))
        else:
            return None
    except (ValueError, OverflowError, OSError):
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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
