"""Turns an app's repo setting into a Source for its forge."""
from urllib.parse import urlparse

from .base import Asset, Release, RepoInfo, Source, SourceError
from .forgejo import Forgejo
from .github import GitHub

KNOWN_HOSTS = {
    "github.com": "github",
    "codeberg.org": "forgejo",
    "gitea.com": "gitea",
    "gitlab.com": "gitlab",
}


def forge_for(repo, forge=None):
    if "://" not in repo:
        return "github"
    host = (urlparse(repo).hostname or "").lower()
    return forge or KNOWN_HOSTS.get(host)


def resolve(repo, forge=None):
    kind = forge_for(repo, forge)
    if kind == "github":
        if "://" in repo:
            path = urlparse(repo).path.strip("/").removesuffix(".git")
            if path.count("/") != 1:
                raise SourceError(f"{repo}: expected https://github.com/owner/repo")
            repo = path
        return GitHub(repo)
    if kind is None:
        raise SourceError(f"{repo}: unknown forge; set 'forge:' to one of github, forgejo, gitea, gitlab")
    if kind in ("forgejo", "gitea"):
        url = urlparse(repo)
        parts = [p for p in url.path.removesuffix(".git").split("/") if p]
        if len(parts) < 2:
            raise SourceError(f"{repo}: expected https://host/owner/repo")
        # Instances served under a path, such as https://example.org/git/, keep it in the API base.
        base = f"{url.scheme}://{url.netloc}" + "".join(f"/{p}" for p in parts[:-2])
        return Forgejo(base, "/".join(parts[-2:]))
    raise SourceError(f"{repo}: {kind} is not supported yet")


__all__ = ["Asset", "Release", "RepoInfo", "Source", "SourceError", "forge_for", "resolve"]
