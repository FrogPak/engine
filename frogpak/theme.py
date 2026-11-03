"""Turns the pond's theme colors into the landing page's light and dark palettes."""
import math

from . import log

LIGHT = {"bg": "#fafafa", "card": "#ffffff", "fg": "#1e1e1e", "muted": "#5e5c64",
         "border": "#deddda", "accent": "#1c71d8", "code": "#f0f0f0"}
DARK = {"bg": "#242424", "card": "#303030", "fg": "#ffffff", "muted": "#c0bfbc",
        "border": "#454545", "accent": "#78aeed", "code": "#1e1e1e"}
WHITE, BLACK, INK = "#ffffff", "#000000", "#1e1e1e"
TEXT_CONTRAST = 4.5


def rgb(color):
    color = color.lstrip("#")
    if len(color) == 3:
        color = "".join(c * 2 for c in color)
    return tuple(int(color[i:i + 2], 16) / 255 for i in (0, 2, 4))


def hex_color(values):
    return "#" + "".join(f"{round(max(0, min(1, v)) * 255):02x}" for v in values)


def mix(color, other, amount):
    """color moved amount (0 to 1) of the way toward other."""
    return hex_color(a + (b - a) * amount for a, b in zip(rgb(color), rgb(other)))


def luminance(color):
    def channel(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in rgb(color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def readable_on(background):
    return max((WHITE, INK), key=lambda c: contrast(c, background))


def surfaces(bg):
    """Text and surface colors derived from a custom background."""
    fg = readable_on(bg)
    light = luminance(bg) > 0.5
    return {
        "bg": bg,
        "fg": fg,
        "muted": mix(fg, bg, 0.3),
        "card": mix(bg, WHITE, 0.7 if light else 0.06),
        "code": mix(bg, BLACK, 0.04 if light else 0.2),
        "border": mix(bg, BLACK if light else WHITE, 0.12),
    }


def fit_accent(accent, palette):
    """Moves a derived accent toward white or black until it reads on every surface."""
    target = WHITE if luminance(palette["bg"]) < 0.5 else BLACK
    for step in range(21):
        candidate = mix(accent, target, step / 20)
        if worst_contrast(candidate, palette) >= TEXT_CONTRAST:
            return candidate
    return mix(accent, target, 1)


def worst_contrast(accent, palette):
    return min(contrast(accent, palette[k]) for k in ("bg", "card", "code"))


def palettes(theme):
    """Light and dark palettes; explicit colors are kept and only warned about."""
    light, dark = dict(LIGHT), dict(DARK)
    if "background" in theme:
        light.update(surfaces(theme["background"]))
    if "background-dark" in theme:
        dark.update(surfaces(theme["background-dark"]))
    elif "background" in theme:
        dark.update(surfaces(mix(theme["background"], BLACK, 0.86)))

    if "accent" in theme:
        light["accent"] = theme["accent"]
    elif "background" in theme:
        light["accent"] = fit_accent(LIGHT["accent"], light)
    if "accent-dark" in theme:
        dark["accent"] = theme["accent-dark"]
    elif "accent" in theme or "background-dark" in theme or "background" in theme:
        dark["accent"] = fit_accent(light["accent"], dark)

    for name, palette, default, key in (("light", light, LIGHT, "accent"), ("dark", dark, DARK, "accent-dark")):
        palette["on-accent"] = readable_on(palette["accent"])
        if palette["accent"] == default["accent"] and palette["bg"] == default["bg"]:
            continue
        ratio = worst_contrast(palette["accent"], palette)
        if ratio < TEXT_CONTRAST:
            source = f"pond.theme.{key}" if key in theme else f"The derived {name} accent"
            log.warning(f"{source} {palette['accent']} is hard to read in {name} mode "
                        f"(contrast {math.floor(ratio * 10) / 10}:1; text needs 4.5:1). "
                        f"{fit_accent(palette['accent'], palette)} would pass.")
    return light, dark


def css_variables(palette):
    return " ".join(f"--{k}: {v};" for k, v in palette.items())
