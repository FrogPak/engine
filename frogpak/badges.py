"""Writes the Pond's README badges: a store-style button in light and dark, and a version badge per app."""
import base64
import html
from dataclasses import dataclass, field
from pathlib import Path
from xml.sax.saxutils import escape

from . import images, theme

DIR = "badges"
BUTTON_LIGHT = f"{DIR}/button-light.svg"
BUTTON_DARK = f"{DIR}/button-dark.svg"
PAGE = f"{DIR}/"
FONT = "Verdana,'DejaVu Sans',Geneva,sans-serif"
# Advance widths of ASCII 32-126 in DejaVu Sans, per 100 px of font size. Text is also
# given textLength, so a viewer's different fallback font is squeezed to the same width
# instead of overflowing the shape.
REGULAR = (32, 40, 46, 84, 64, 95, 78, 27, 39, 39, 50, 84, 32, 36, 32, 34, 64, 64, 64, 64, 64, 64, 64, 64, 64,
           64, 34, 34, 84, 84, 84, 53, 100, 68, 69, 70, 77, 63, 58, 77, 75, 30, 30, 66, 56, 86, 75, 79, 60, 79,
           69, 63, 61, 73, 68, 99, 68, 61, 68, 39, 34, 39, 84, 50, 50, 61, 63, 55, 63, 62, 35, 63, 63, 28, 28,
           58, 28, 97, 63, 61, 63, 63, 41, 52, 39, 63, 59, 82, 59, 59, 52, 64, 34, 64, 84)
BOLD = (35, 46, 52, 84, 70, 100, 87, 31, 46, 46, 52, 84, 38, 42, 38, 37, 70, 70, 70, 70, 70, 70, 70, 70, 70, 70,
        40, 40, 84, 84, 84, 58, 100, 77, 76, 73, 83, 68, 68, 82, 84, 37, 37, 77, 64, 100, 84, 85, 73, 85, 77, 72,
        68, 81, 77, 110, 77, 72, 73, 46, 37, 46, 84, 50, 50, 67, 72, 59, 72, 68, 44, 72, 71, 34, 34, 66, 34, 104,
        71, 69, 72, 72, 49, 60, 48, 71, 65, 92, 64, 65, 58, 71, 37, 71, 84)
LABEL_GRAY = "#555555"
BUTTONS = {
    "light": {"bg": "#ffffff", "border": "#c0bfbc", "fg": "#1e1e1e", "muted": "#5e5c64"},
    "dark": {"bg": "#1e1e1e", "border": "#5e5c64", "fg": "#ffffff", "muted": "#c0bfbc"},
}


@dataclass
class Made:
    button_width: int
    # App ID -> its version badge's path in the site.
    versions: dict = field(default_factory=dict)


def text_width(text, size, bold=False):
    table = BOLD if bold else REGULAR
    wide = max(table)
    return sum(table[ord(c) - 32] if 32 <= ord(c) < 127 else wide for c in text) * size / 100


def credit(pond):
    """Alt and hover text for every badge."""
    return f"{pond.title}, published with FrogPak"


def version_badge(label, value, accent, title):
    """A flat badge: label on gray, value on the Pond's accent."""
    size, pad, height = 11, 6, 20
    lw = round(text_width(label, size) + 2 * pad)
    vw = round(text_width(value, size) + 2 * pad)
    width = lw + vw
    fg = theme.readable_on(accent)
    shadow = "#010101" if fg == theme.WHITE else "#ffffff"
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" role="img" '
        f'aria-label="{escape(title, {chr(34): "&quot;"})}">',
        f"<title>{escape(title)}</title>",
        f'<clipPath id="r"><rect width="{width}" height="{height}" rx="3"/></clipPath>',
        '<g clip-path="url(#r)">',
        f'<rect width="{lw}" height="{height}" fill="{LABEL_GRAY}"/>',
        f'<rect x="{lw}" width="{vw}" height="{height}" fill="{accent}"/>',
        "</g>",
        f'<g font-family="{FONT}" font-size="{size}" text-anchor="middle">',
    ]
    for x, w, text, color, glow in ((lw / 2, lw, label, theme.WHITE, "#010101"), (lw + vw / 2, vw, value, fg, shadow)):
        length = round(w - 2 * pad)
        common = f'x="{x:g}" textLength="{length}" lengthAdjust="spacingAndGlyphs"'
        parts.append(f'<text {common} y="15" fill="{glow}" fill-opacity=".3">{escape(text)}</text>')
        parts.append(f'<text {common} y="14" fill="{color}">{escape(text)}</text>')
    parts.append("</g></svg>\n")
    return "".join(parts)


def button_width(pond_title):
    pad, icon, gap = 10, 32, 10
    tw = max(text_width("Get it on", 11), text_width(pond_title, 18, bold=True))
    return round(pad + icon + gap + tw + pad + 4)


def button(pond_title, icon_png, colors, title):
    """A store-style button: the Pond's icon, "Get it on" and the Pond's name."""
    height, pad, icon, gap = 48, 10, 32, 10
    small, big = 11, 18
    width = button_width(pond_title)
    x = pad + icon + gap
    uri = "data:image/png;base64," + base64.b64encode(icon_png).decode()
    return "".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" '
        f'height="{height}" role="img" aria-label="{escape(title, {chr(34): "&quot;"})}">',
        f"<title>{escape(title)}</title>",
        f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="8" fill="{colors["bg"]}" '
        f'stroke="{colors["border"]}"/>',
        f'<image x="{pad}" y="{(height - icon) / 2:g}" width="{icon}" height="{icon}" href="{uri}" xlink:href="{uri}"/>',
        f'<g font-family="{FONT}">',
        f'<text x="{x}" y="19" font-size="{small}" fill="{colors["muted"]}" '
        f'textLength="{round(text_width("Get it on", small))}" lengthAdjust="spacingAndGlyphs">Get it on</text>',
        f'<text x="{x}" y="37" font-size="{big}" font-weight="bold" fill="{colors["fg"]}" '
        f'textLength="{round(text_width(pond_title, big, bold=True))}" lengthAdjust="spacingAndGlyphs">'
        f"{escape(pond_title)}</text>",
        "</g></svg>\n",
    ])


def _icon_png(image, folder):
    path = folder / "icon.png"
    images.render_png(images._square_svg(image, 64), path, 64, 64)
    data = path.read_bytes()
    path.unlink()
    return data


def write(site, pond, entries, icon, icon_dark):
    """Writes the buttons and each app's version badge; returns a Made."""
    out = Path(site) / DIR
    out.mkdir(exist_ok=True)
    title = credit(pond)
    pngs = {"light": _icon_png(icon, out)}
    pngs["dark"] = pngs["light"] if icon_dark is icon else _icon_png(icon_dark, out)
    for mode, path in (("light", BUTTON_LIGHT), ("dark", BUTTON_DARK)):
        (Path(site) / path).write_text(button(pond.title, pngs[mode], BUTTONS[mode], title))
    # The accent of the appearance the landing page starts in; its text color is picked to contrast.
    light, dark = theme.palettes(pond.theme)
    accent = (dark if pond.mode == "dark" else light)["accent"]
    made = Made(button_width(pond.title))
    for entry in entries:
        name = f"{DIR}/{entry['id']}.svg"
        value = f"v{entry['version']}" if entry["version"] else "available"
        (Path(site) / name).write_text(version_badge(pond.title, value, accent, title))
        made.versions[entry["id"]] = name
    return made



def button_snippets(pond, base_url):
    """The button for READMEs, linking to the Pond's page: as HTML, which switches with GitHub's
    light and dark mode, and as Markdown, which shows the light version only."""
    alt = credit(pond)
    html_snippet = (f'<a href="{base_url}"><picture>'
                    f'<source media="(prefers-color-scheme: dark)" srcset="{base_url}{BUTTON_DARK}">'
                    f'<img src="{base_url}{BUTTON_LIGHT}" alt="{html.escape(alt)}" height="48"></picture></a>')
    markdown = f"[![{_md(alt)}]({base_url}{BUTTON_LIGHT})]({base_url})"
    return html_snippet, markdown


def badge_snippet(pond, base_url, app_id, badge_name):
    """An app's version badge as Markdown, linking to the app's card."""
    return f"[![{_md(credit(pond))}]({base_url}{badge_name})]({base_url}#{app_id})"


def _md(text):
    """Text safe inside Markdown image brackets."""
    return text.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")
