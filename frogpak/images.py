"""Resolves the Pond's logo and favicon and renders the PNG sizes browsers and software centers need."""
import base64
import re
import struct
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import http, log

DATA = Path(__file__).parent / "data"
MAX_BYTES = 2 * 1024 * 1024
SQUARE_TOLERANCE = 1.25
# Square PNGs written to the site; ICON is also the Icon of index.flatpakrepo.
FAVICON = "favicon-32.png"
TOUCH_ICON = "apple-touch-icon.png"
ICON = "icon-256.png"
PNG_SIZES = {FAVICON: 32, TOUCH_ICON: 180, "icon-192.png": 192, ICON: 256}


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


def _find_default(pond_dir, stem):
    for ext in (".svg", ".png"):
        path = Path(pond_dir) / f"{stem}{ext}"
        if path.is_file():
            return path.name
    return None


def resolve(pond, pond_dir):
    """Returns (logo, dark logo or None, favicon source)."""
    logo = None
    spec = pond.logo or _find_default(pond_dir, "logo")
    if spec:
        logo = _load(spec, pond_dir)
    custom = logo is not None
    if logo is None:
        logo = Image((DATA / "default-logo.svg").read_bytes(), "svg", "FrogPak default logo")

    dark = None
    spec = pond.logo_dark or (_find_default(pond_dir, "logo-dark") if custom else None)
    if spec:
        dark = _load(spec, pond_dir, "no dark logo")

    favicon = _load(pond.favicon, pond_dir, "using the logo") if pond.favicon else None
    if favicon is None:
        favicon = logo
        ratio = aspect(logo)
        if ratio and ratio > SQUARE_TOLERANCE:
            log.warning(f"{logo.origin} is not square ({ratio:.2f}:1); the favicon may look poor. "
                        "Set pond.favicon to a square image.")
    return logo, dark, favicon


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


def write_icons(image, site):
    site = Path(site)
    for name, side in PNG_SIZES.items():
        render_png(_square_svg(image, side), site / name, side, side)
    ratio = aspect(image)
    if image.kind == "svg" and not image.external and ratio and ratio < 1.01:
        (site / "favicon.svg").write_bytes(image.data)
        return True
    return False
