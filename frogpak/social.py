"""The image shown when someone shares a link to the Pond's page.

pond.social-image, when set, is used. Otherwise, on GitHub, the image uploaded as the
repository's social preview (Settings > General > Social preview). Without either,
the page offers the Pond's icon, which apps show as a small card.
"""
import os
from pathlib import Path
from urllib.parse import urlparse

from . import http, images, log

QUERY = ("query($owner: String!, $name: String!) "
         "{ repository(owner: $owner, name: $name) { openGraphImageUrl usesCustomOpenGraphImage } }")
STEM = "social"
KINDS = {"png": ".png", "jpeg": ".jpg"}


def kind(data):
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    return None


def repository_image(warn=True):
    """The repository's uploaded social preview image, as an https URL, or None.

    None also when GitHub shows only its generated card, which is about the repository
    rather than the Pond. Needs GITHUB_REPOSITORY and GITHUB_TOKEN, as in Actions.
    """
    repository, token = os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_TOKEN")
    if "/" not in repository or not token:
        return None
    owner, name = repository.split("/", 1)
    api = os.environ.get("GITHUB_GRAPHQL_URL", "https://api.github.com/graphql")
    try:
        reply = http.post_json(api, {"query": QUERY, "variables": {"owner": owner, "name": name}},
                               {"Authorization": f"Bearer {token}"})
    except (http.HTTPError, http.NetworkError, ValueError) as error:
        if warn:
            log.warning(f"cannot look up the repository's social preview image ({error}); "
                        f"the page offers the icon instead")
        return None
    found = ((reply or {}).get("data") or {}).get("repository") or {}
    url = found.get("openGraphImageUrl") or ""
    if found.get("usesCustomOpenGraphImage") and urlparse(url).scheme == "https":
        return url
    return None


def source(pond, warn=True):
    """Where the image comes from: pond.social-image, the repository's, or None."""
    return pond.social_image or repository_image(warn)


def identity(spec, pond_dir):
    """What poll compares for the image from source(), so a new image republishes the page.
    A file is identified by its contents, a URL by itself: GitHub gives each uploaded image
    a new address."""
    return images.identity(spec, pond_dir)


def write(site, spec, pond_dir):
    """Copies the image from source() into the site; returns its file name, or None for the icon."""
    if not spec:
        return None
    if spec.startswith("http://"):
        log.warning(f"{spec}: URLs must use https; the page offers the icon instead")
        return None
    # The repository's image is GitHub's, not a file of the Pond, so it is fetched as a URL.
    loaded = images.read_file(spec, pond_dir, "the page offers the icon instead")
    if loaded is None:
        return None
    data = loaded[0]
    found = kind(data)
    if found is None:
        log.warning(f"{spec}: not a PNG or JPEG image; the page offers the icon instead")
        return None
    name = STEM + KINDS[found]
    (Path(site) / name).write_bytes(data)
    return name
