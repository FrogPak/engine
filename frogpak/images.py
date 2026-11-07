"""Resolves the Pond's logo and favicon and renders the PNG sizes browsers and software centers need."""
import base64
import hashlib
import re
import struct
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import http, log

DATA = Path(__file__).parent / "data"
MAX_BYTES = 2 * 1024 * 1024
SQUARE_TOLERANCE = 1.25
# Square PNGs written to the site. Browsers use the favicon sizes, which pond.favicon can override;
# the icon sizes are the Pond's own, and ICON is also the Icon of index.flatpakrepo.
FAVICON = "favicon-32.png"
TOUCH_ICON = "apple-touch-icon.png"
ICON = "icon-256.png"
FAVICON_SIZES = {FAVICON: 32, TOUCH_ICON: 180}
ICON_SIZES = {"icon-192.png": 192, ICON: 256}


@dataclass
class Image:
    data: bytes
    kind: str          # "svg" or "png"
    origin: str        # for messages
    external: bool = False

    @property
    def ext(self):
        return f".{self.kind}"


def sniff(data):
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    head = data[:2048].lstrip(b"\xef\xbb\xbf \t\r\n")
    if head.startswith((b"<?xml", b"<svg", b"<!--", b"<!DOCTYPE svg")) and b"<svg" in data[:4096]:
        return "svg"
    return None


def read_file(spec, pond_dir, fallback):
    """Reads a Pond repository path or an https URL; returns (bytes, external) or None with a warning."""
    try:
        if spec.startswith("http://"):
            log.warning(f"{spec}: URLs must use https; {fallback}")
            return None
        if spec.startswith("https://"):
            return http.get_bytes(spec, limit=MAX_BYTES), True
        base = Path(pond_dir).resolve()
        path = (base / spec).resolve()
        if base not in path.parents:
            log.warning(f"{spec}: paths must stay inside the Pond repository; {fallback}")
            return None
        if path.stat().st_size > MAX_BYTES:
            log.warning(f"{spec}: larger than 2 MB; {fallback}")
            return None
        return path.read_bytes(), False
    except (OSError, http.HTTPError, http.NetworkError) as error:
        log.warning(f"{spec}: cannot be read ({error}); {fallback}")
        return None


def _load(spec, pond_dir, fallback="using the default"):
    """Reads an image from a repo path or URL; returns None with a warning on any failure."""
    result = read_file(spec, pond_dir, fallback)
    if result is None:
        return None
    data, external = result
    kind = sniff(data)
    if kind is None:
        log.warning(f"{spec}: not an SVG or PNG image; {fallback}")
        return None
    return Image(data, kind, spec, external)


def identity(spec, pond_dir):
    """What poll compares for a file the page uses, so changing it republishes: a repository
    file by its contents, a URL by itself. None for no file, or one that cannot be read."""
    if not spec or spec.startswith(("https://", "http://")):
        return spec or None
    base = Path(pond_dir).resolve()
    path = (base / spec).resolve()
    if base not in path.parents:
        return None
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _find_default(pond_dir, stem):
    for ext in (".svg", ".png"):
        path = Path(pond_dir) / f"{stem}{ext}"
        if path.is_file():
            return path.name
    return None


@dataclass
class Logos:
    """Which image goes where. The header is the wide logo when there is one, else the square one."""
    header: Image
    header_dark: Image | None
    wide: bool
    favicon: Image
    icon: Image
    badge: Image
    badge_dark: Image


def _specs(pond, pond_dir):
    """The file for each logo role: the key, its deprecated stand-in, then a file found at the root.
    Dark versions are looked for at the root only when their light version is the Pond's own."""
    square = pond.logo_square or pond.logo or _find_default(pond_dir, "logo-square") or _find_default(pond_dir, "logo")
    wide = pond.logo_wide or _find_default(pond_dir, "logo-wide")
    return {
        "logo-square": square,
        "logo-square-dark": pond.logo_square_dark or pond.logo_dark or (
            (_find_default(pond_dir, "logo-square-dark") or _find_default(pond_dir, "logo-dark")) if square else None),
        "logo-wide": wide,
        "logo-wide-dark": pond.logo_wide_dark or (_find_default(pond_dir, "logo-wide-dark") if wide else None),
        "favicon": pond.favicon,
    }


def _deprecations(pond, pond_dir):
    if pond.logo:
        log.notice("pond.logo is deprecated; rename it to logo-square, or use logo-wide for a logo with the "
                   "Pond's name in it")
    if pond.logo_dark:
        log.notice("pond.logo-dark is deprecated; rename it to logo-square-dark, or use logo-wide-dark")
    for old, new in (("logo", "logo-square"), ("logo-dark", "logo-square-dark")):
        found = _find_default(pond_dir, old)
        if found and not getattr(pond, new.replace("-", "_")) and not _find_default(pond_dir, new):
            log.notice(f"{found} is still used, but the name is deprecated; rename it to {new}{Path(found).suffix}")


def resolve(pond, pond_dir):
    """Loads the Pond's logos and decides where each is used; returns a Logos."""
    _deprecations(pond, pond_dir)
    specs = _specs(pond, pond_dir)
    square = _load(specs["logo-square"], pond_dir) if specs["logo-square"] else None
    wide = _load(specs["logo-wide"], pond_dir, "no wide logo") if specs["logo-wide"] else None
    square_dark = (_load(specs["logo-square-dark"], pond_dir, "no dark square logo")
                   if square and specs["logo-square-dark"] else None)
    wide_dark = (_load(specs["logo-wide-dark"], pond_dir, "no dark wide logo")
                 if wide and specs["logo-wide-dark"] else None)
    if square is None and wide is None:
        square = Image((DATA / "default-logo.svg").read_bytes(), "svg", "FrogPak default logo")

    if square is None:
        log.warning("pond.logo-square is not set, so the favicon, the remote's icon and the badge button may use "
                    f"{wide.origin} shrunk to a square. Set pond.logo-square to a square version of the logo.")
    else:
        ratio = aspect(square)
        if ratio and ratio > SQUARE_TOLERANCE:
            log.warning(f"{square.origin} is not square ({ratio:.2f}:1), so the favicon, the remote's icon and the "
                        "badge button may look poor. Use a square image for pond.logo-square.")

    favicon = _load(pond.favicon, pond_dir, "using the square logo") if pond.favicon else None
    icon = square or wide
    icon_dark = (square_dark or square) if square else (wide_dark or wide)
    return Logos(header=wide or square, header_dark=wide_dark if wide else square_dark, wide=wide is not None,
                 favicon=favicon or icon, icon=icon, badge=icon, badge_dark=icon_dark)


def identities(pond, pond_dir):
    """identity() for each file the landing page is built from, including logos found at the root."""
    specs = _specs(pond, pond_dir)
    specs["css"] = pond.css
    return {key: identity(spec, pond_dir) for key, spec in specs.items()}


def _length(value):
    match = re.match(r"\s*([0-9.]+)\s*(px)?\s*$", value or "")
    return float(match.group(1)) if match else None


def size(image):
    """(width, height) in the image's own units, or None when unknown."""
    if image.kind == "png":
        width, height = struct.unpack(">II", image.data[16:24])
        return width, height
    head = image.data[:8192].decode("utf-8", "replace")
    tag = re.search(r"<svg\b[^>]*>", head, re.S)
    if not tag:
        return None
    attrs = dict(re.findall(r'([\w:-]+)\s*=\s*["\']([^"\']*)["\']', tag.group(0)))
    viewbox = attrs.get("viewBox", "").replace(",", " ").split()
    if len(viewbox) == 4:
        try:
            return float(viewbox[2]), float(viewbox[3])
        except ValueError:
            pass
    width, height = _length(attrs.get("width")), _length(attrs.get("height"))
    return (width, height) if width and height else None


def aspect(image):
    dims = size(image)
    if not dims or not all(dims):
        return None
    width, height = dims
    return max(width, height) / min(width, height)


def _square_svg(image, side):
    """Wraps the image, centerd and scaled to fit, in a square SVG."""
    mime = "image/svg+xml" if image.kind == "svg" else "image/png"
    uri = f"data:{mime};base64,{base64.b64encode(image.data).decode()}"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{side}" height="{side}" viewBox="0 0 {side} {side}">'
            f'<image width="{side}" height="{side}" preserveAspectRatio="xMidYMid meet" '
            f'xlink:href="{uri}" href="{uri}"/></svg>')


def render_png(svg_text, dest, width, height):
    result = subprocess.run(["rsvg-convert", "-w", str(width), "-h", str(height), "-o", str(dest)],
                            input=svg_text.encode(), capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"rsvg-convert failed: {result.stderr.decode(errors='replace').strip()}")


def write_logo(image, site, stem):
    """Writes the logo for the page header; returns its file name.

    SVGs from URLs are published as PNG renders, so third-party SVG content
    is never served from the Pond's origin.
    """
    site = Path(site)
    if image.kind == "svg" and image.external:
        dims = size(image) or (1, 1)
        scale = 512 / max(dims)
        width, height = max(1, round(dims[0] * scale)), max(1, round(dims[1] * scale))
        mime_uri = base64.b64encode(image.data).decode()
        wrapper = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                   f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                   f'<image width="{width}" height="{height}" '
                   f'xlink:href="data:image/svg+xml;base64,{mime_uri}"/></svg>')
        name = f"{stem}.png"
        render_png(wrapper, site / name, width, height)
        return name
    name = f"{stem}{image.ext}"
    (site / name).write_bytes(image.data)
    return name


def write_icons(favicon, icon, site):
    """Writes the browser icons from favicon and the Pond's icons from icon; returns whether
    favicon.svg was written."""
    site = Path(site)
    for image, sizes in ((favicon, FAVICON_SIZES), (icon, ICON_SIZES)):
        for name, side in sizes.items():
            render_png(_square_svg(image, side), site / name, side, side)
    ratio = aspect(favicon)
    if favicon.kind == "svg" and not favicon.external and ratio and ratio < 1.01:
        (site / "favicon.svg").write_bytes(favicon.data)
        return True
    return False
