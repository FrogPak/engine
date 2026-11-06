"""Writes the landing page and apps.json into the published site."""
import html
import json
from urllib.parse import urlparse
from pathlib import Path

from . import config, images, licenses, theme

STATE_FILE = "apps.json"
GITHUB_MARK = (
    '<svg class="mark" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">'
    '<path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>'
    "</svg>"
)

PAGE = """<!doctype html>
<html lang="en"{mode_attr}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>
// The visitor's appearance choice, applied before the page draws so it never flashes the other one.
try {{
  const mode = localStorage.getItem("frogpak-mode");
  if (mode === "system") delete document.documentElement.dataset.mode;
  else if (mode === "light" || mode === "dark") document.documentElement.dataset.mode = mode;
}} catch (error) {{}}
</script>
<title>{title}</title>
{social}
{favicons}
<style>
:root {{ {light} color-scheme: light; }}
:root[data-mode="dark"] {{ {dark} color-scheme: dark; }}
@media (prefers-color-scheme: dark) {{
  :root:not([data-mode="light"]) {{ {dark} color-scheme: dark; }}
}}
.brand .logo-dark {{ display: none; }}
:root[data-mode="dark"] .brand .logo-light {{ display: none; }}
:root[data-mode="dark"] .brand .logo-dark {{ display: block; }}
@media (prefers-color-scheme: dark) {{
  :root:not([data-mode="light"]) .brand .logo-light {{ display: none; }}
  :root:not([data-mode="light"]) .brand .logo-dark {{ display: block; }}
}}
[hidden] {{ display: none !important; }}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; background: var(--bg); color: var(--fg);
  font: 16px/1.5 system-ui, -apple-system, "Cantarell", "Segoe UI", sans-serif;
}}
main {{ max-width: 44rem; margin: 0 auto; padding: 2rem 1rem 4rem; }}
h1 {{ font-size: 1.75rem; margin: 0; }}
.top {{ display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: .75rem 1rem; margin-bottom: .25rem; }}
.top-end {{ display: flex; align-items: center; gap: 1rem; margin-left: auto; }}
.brand {{ display: flex; align-items: center; gap: .75rem; min-width: 0; }}
.brand img {{ height: 44px; width: auto; max-width: 10rem; object-fit: contain; flex: none; }}
.mark {{ vertical-align: -2px; margin-right: .3rem; }}
h2 {{ font-size: 1.15rem; margin: 2rem 0 .75rem; }}
.apps-head {{
  display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between;
  gap: .5rem 1rem; margin: 2rem 0 .75rem;
}}
.apps-head h2 {{ margin: 0; }}
.toggle {{ display: flex; }}
.toggle button {{
  font: inherit; font-size: .85rem; padding: .25rem .8rem; cursor: pointer;
  color: var(--fg); background: var(--card); border: 1px solid var(--border);
}}
.toggle button + button {{ border-left: none; }}
.toggle button:first-child {{ border-radius: 8px 0 0 8px; }}
.toggle button:last-child {{ border-radius: 0 8px 8px 0; }}
.toggle button[aria-pressed="true"] {{ background: var(--accent); border-color: var(--accent); color: var(--on-accent); }}
.mode-picker button {{ display: grid; place-items: center; padding: .3rem .55rem; }}
.mode-picker svg {{ width: 1.1rem; height: 1.1rem; }}
p {{ margin: 0 0 1rem; color: var(--muted); }}
a {{ color: var(--accent); }}
.card {{
  background: var(--card); border: 1px solid var(--border);
  border-radius: 12px; padding: 1rem; margin-bottom: .75rem;
}}
.app {{ display: flex; gap: 1rem; align-items: flex-start; }}
.icon {{
  flex: none; width: 64px; height: 64px; border-radius: 14px;
  background: var(--code); display: grid; place-items: center;
  font-size: 1.75rem; color: var(--muted);
}}
.icon img {{ width: 64px; height: 64px; }}
.body {{ min-width: 0; flex: 1; }}
.app h3 {{ margin: 0; font-size: 1.1rem; min-width: 0; overflow-wrap: break-word; }}
/* The version wraps whole, under the name, rather than splitting. */
.app h3 small {{ display: inline-block; white-space: nowrap; color: var(--muted); font-weight: normal; font-size: .85rem; }}
.app p {{ margin: .25rem 0 .75rem; }}
.badge {{
  display: inline-block; font-size: .8rem; line-height: 1.4; color: var(--muted);
  border: 1px solid var(--border); border-radius: 999px; padding: .05rem .6rem;
}}
.facts {{ display: flex; flex-wrap: wrap; gap: .35rem; margin: 0 0 .75rem; }}
.links {{ display: flex; flex-wrap: wrap; gap: .3rem 1rem; font-size: .9rem; margin-top: .6rem; }}
.links a {{ white-space: nowrap; }}
.cmd {{
  display: flex; align-items: flex-start; gap: .5rem; background: var(--code);
  border-radius: 8px; padding: .5rem .75rem;
}}
.cmd code {{
  flex: 1; min-width: 0; overflow-wrap: anywhere;
  font: .85rem ui-monospace, "Source Code Pro", monospace;
}}
.cmd button {{
  flex: none; display: grid; place-items: center; width: 2rem; height: 2rem; margin: -.25rem -.4rem -.25rem 0;
  color: var(--accent); background: none; border: none; border-radius: 6px; cursor: pointer;
}}
.cmd button:hover {{ background: var(--card); }}
.cmd button svg {{ width: 1.25rem; height: 1.25rem; }}
.cmd button .done, .cmd button.copied .copy {{ display: none; }}
.cmd button.copied .done {{ display: block; }}
.visually-hidden {{
  position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap;
}}
.head {{ display: flex; align-items: flex-start; justify-content: space-between; gap: .5rem .75rem; }}
.install {{ position: relative; display: flex; flex: none; }}
.install-main, .install summary {{
  background: var(--accent); color: var(--on-accent); cursor: pointer;
}}
.install-main {{
  font-weight: 600; font-size: .95rem; text-decoration: none;
  padding: .4rem 1.1rem; border-radius: 8px 0 0 8px;
}}
.install summary {{
  list-style: none; display: grid; place-items: center; height: 100%; padding: 0 .55rem;
  border-left: 1px solid color-mix(in srgb, var(--on-accent) 35%, transparent); border-radius: 0 8px 8px 0;
}}
.install summary::-webkit-details-marker {{ display: none; }}
.install summary svg {{ width: 1rem; height: 1rem; transition: transform .15s; }}
.install details[open] summary svg {{ transform: rotate(180deg); }}
.install-main:hover, .install summary:hover {{ filter: brightness(.92); }}
.install-menu {{
  position: absolute; right: 0; top: calc(100% + .4rem); z-index: 10; width: min(21rem, calc(100vw - 2.25rem));
  background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: .75rem;
  box-shadow: 0 8px 24px rgb(0 0 0 / .2);
}}
.install-menu p {{ font-size: .85rem; margin: .75rem 0 .35rem; }}
.scope-picker {{ display: flex; }}
.scope-picker button {{
  flex: 1; font: inherit; font-size: .9rem; padding: .35rem .9rem; cursor: pointer;
  color: var(--fg); background: var(--card); border: 1px solid var(--border); border-bottom: none;
}}
.scope-picker button:first-child {{ border-radius: 8px 0 0 0; }}
.scope-picker button:last-child {{ border-radius: 0 8px 0 0; border-left: none; }}
.scope-picker button[aria-pressed="true"] {{ background: var(--accent); border-color: var(--accent); color: var(--on-accent); }}
.scope-picker + .cmd {{ border-radius: 0 0 8px 8px; }}
.hint {{ font-size: .9rem; margin: .6rem 0 0; }}
/* On the narrowest screens the Install button goes under the name instead of past the card's edge. */
@media (max-width: 22rem) {{
  .head {{ flex-wrap: wrap; position: relative; }}
  /* The menu then opens from the card's text column rather than from the button's right edge. */
  .install {{ position: static; }}
  .install-menu {{ width: auto; left: calc(-64px - 1rem); }}
}}
footer {{ margin-top: 3rem; font-size: .85rem; color: var(--muted); text-align: center; }}
</style>
{custom_css}
</head>
<body>
<main>
<div class="top">
<div class="brand">{logo}<h1>{title}</h1></div>
<div class="top-end">{source}{mode_picker}</div>
</div>
{subtitle}

<h2>Add the repository</h2>
<div class="card">
<div class="scope-picker" role="group" aria-label="Installation">
<button type="button" data-scope="system" aria-pressed="true">System</button>
<button type="button" data-scope="user" aria-pressed="false">User</button>
</div>
<div class="cmd"><code>flatpak remote-add<span class="scope"></span> --if-not-exists {remote} {base_url}index.flatpakrepo</code>{copy}</div>
<p class="hint" data-for="system">For everyone on this computer. May ask for your password.</p>
<p class="hint" data-for="user" hidden>For your account only. No password needed.</p>
</div>

<div class="apps-head"><h2>Apps</h2>{arch_picker}</div>
{apps}
<p class="no-apps" hidden></p>
<footer>{updated}Published with <a href="https://github.com/FrogPak/engine">FrogPak</a></footer>
</main>
<script>
const MODE_KEY = "frogpak-mode";
function showMode() {{
  const mode = document.documentElement.dataset.mode || "system";
  for (const button of document.querySelectorAll("[data-mode-choice]")) button.setAttribute("aria-pressed", String(button.dataset.modeChoice === mode));
}}
for (const button of document.querySelectorAll("[data-mode-choice]")) {{
  button.addEventListener("click", () => {{
    const mode = button.dataset.modeChoice;
    if (mode === "system") delete document.documentElement.dataset.mode;
    else document.documentElement.dataset.mode = mode;
    try {{ localStorage.setItem(MODE_KEY, mode); }} catch (error) {{}}
    showMode();
  }});
}}
showMode();
const ARCH_KEY = "frogpak-arch";
const archButtons = [...document.querySelectorAll("[data-arch]")];
function setArch(arch) {{
  let shown = 0;
  for (const card of document.querySelectorAll(".card.app")) {{
    card.hidden = arch !== "" && !card.dataset.arches.split(" ").includes(arch);
    if (!card.hidden) shown++;
  }}
  for (const button of archButtons) button.setAttribute("aria-pressed", String(button.dataset.arch === arch));
  const empty = document.querySelector(".no-apps");
  empty.hidden = shown > 0;
  empty.textContent = `No apps for ${{arch}} yet.`;
  try {{ localStorage.setItem(ARCH_KEY, arch); }} catch (error) {{}}
}}
for (const button of archButtons) button.addEventListener("click", () => setArch(button.dataset.arch));
if (archButtons.length) {{
  let savedArch = null;
  try {{ savedArch = localStorage.getItem(ARCH_KEY); }} catch (error) {{}}
  setArch(archButtons.some((button) => button.dataset.arch === savedArch) ? savedArch : "");
}}
const SCOPE_KEY = "frogpak-scope";
function setScope(scope) {{
  for (const span of document.querySelectorAll(".scope")) span.textContent = scope === "user" ? " --user" : "";
  for (const button of document.querySelectorAll("[data-scope]")) button.setAttribute("aria-pressed", String(button.dataset.scope === scope));
  for (const hint of document.querySelectorAll("[data-for]")) hint.hidden = hint.dataset.for !== scope;
  try {{ localStorage.setItem(SCOPE_KEY, scope); }} catch (error) {{}}
}}
for (const button of document.querySelectorAll("[data-scope]")) {{
  button.addEventListener("click", () => setScope(button.dataset.scope));
}}
// Dates are written in UTC and shown in the visitor's own time zone and format.
for (const time of document.querySelectorAll("time[data-format]")) {{
  const value = time.getAttribute("datetime");
  const moment = new Date(value);
  if (Number.isNaN(moment.getTime())) continue;
  const options = time.dataset.format === "date" ? {{ dateStyle: "medium" }} : {{ dateStyle: "medium", timeStyle: "short" }};
  // A date with no time is a calendar day, not midnight UTC.
  if (value.length === 10) options.timeZone = "UTC";
  try {{ time.textContent = new Intl.DateTimeFormat(undefined, options).format(moment); }} catch (error) {{}}
}}
let savedScope = null;
try {{ savedScope = localStorage.getItem(SCOPE_KEY); }} catch (error) {{}}
setScope(savedScope === "user" ? "user" : "system");
for (const button of document.querySelectorAll(".cmd button")) {{
  const label = button.querySelector(".visually-hidden");
  button.addEventListener("click", async () => {{
    const code = button.parentElement.querySelector("code");
    try {{
      await navigator.clipboard.writeText(code.textContent);
      button.classList.add("copied");
      label.textContent = "Copied";
    }} catch (error) {{
      // No clipboard access: select the command so it can be copied by hand.
      const range = document.createRange();
      range.selectNodeContents(code);
      getSelection().removeAllRanges();
      getSelection().addRange(range);
      label.textContent = "Selected; copy it with your keyboard";
    }}
    setTimeout(() => {{ button.classList.remove("copied"); label.textContent = "Copy"; }}, 2000);
  }});
}}
// One install menu open at a time; close it with Escape or by clicking elsewhere.
const menus = [...document.querySelectorAll(".install details")];
for (const menu of menus) {{
  menu.addEventListener("toggle", () => {{
    if (menu.open) for (const other of menus) if (other !== menu) other.open = false;
  }});
}}
document.addEventListener("click", (event) => {{
  for (const menu of menus) if (menu.open && !menu.contains(event.target)) menu.open = false;
}});
document.addEventListener("keydown", (event) => {{
  if (event.key !== "Escape") return;
  for (const menu of menus) if (menu.open) {{ menu.open = false; menu.querySelector("summary").focus(); }}
}});
</script>
</body>
</html>
"""

# Two overlapping rounded squares, and a check shown once copied.
COPY_BUTTON = (
    '<button type="button">'
    '<svg class="copy" viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M15.5 6V5.5A2.5 2.5 0 0 0 13 3H5.5A2.5 2.5 0 0 0 3 5.5V13a2.5 2.5 0 0 0 2.5 2.5H6" '
    'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'
    '<rect x="8" y="8" width="13" height="13" rx="3" fill="currentColor"/></svg>'
    '<svg class="done" viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M5 12.5l4.5 4.5L19 7" fill="none" stroke="currentColor" stroke-width="2.5" '
    'stroke-linecap="round" stroke-linejoin="round"/></svg>'
    '<span class="visually-hidden">Copy</span></button>'
)
CHEVRON = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" '
           'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>')

APP = """<div class="card app" data-arches="{arches}">
<div class="icon">{icon}</div>
<div class="body">
<div class="head">
<h3>{name}{version}</h3>
<div class="install">
<a class="install-main" href="{open_url}">Install<span class="visually-hidden"> {name}</span></a>
<details>
<summary>{chevron}<span class="visually-hidden">More ways to install {name}</span></summary>
<div class="install-menu">
<a href="{app_id}.flatpakref" download>Download .flatpakref</a>
<p>Or, once the repository is added, from a terminal:</p>
<div class="cmd"><code>flatpak install<span class="scope"></span> {remote} {app_id}</code>{copy}</div>
</div>
</details>
</div>
</div>
<p>{summary}</p>
<div class="facts">{facts}</div>
<div class="links">{links}</div>
</div>
</div>"""
# Card links from the metainfo, in this order; an app without one simply has no link.
LINK_LABELS = (("homepage", "Website"), ("bugtracker", "Issue tracker"), ("donation", "Donate"))


def _e(value):
    return html.escape(value or "", quote=True)


def _web(url):
    return url if urlparse(url or "").scheme in ("http", "https") else "#"


def time_markup(value, fmt):
    """A <time> the page script shows in the visitor's time zone; UTC text until it runs."""
    fallback = value[:10] if fmt == "date" or len(value) == 10 else value[:16].replace("T", " ") + " UTC"
    return f'<time datetime="{_e(value)}" data-format="{fmt}">{_e(fallback)}</time>'


def license_markup(expression):
    """The license with each SPDX ID linked to its page."""
    if not expression:
        return '<span class="badge">License not stated</span>'
    pieces = []
    for text, url in licenses.parts(expression):
        pieces.append(f'<a href="{_e(url)}">{_e(text)}</a>' if url else _e(text))
    # Parentheses hug what they enclose.
    joined = " ".join(pieces).replace("( ", "(").replace(" )", ")")
    return f'<span class="badge" title="License">{joined}</span>'


def links_markup(entry):
    """Source, then the metainfo's links that are https. A homepage that is the repository is left out."""
    source = _web(entry["url"])
    links = [f'<a href="{_e(source)}">{GITHUB_MARK}Source</a>']
    found = entry.get("links") or {}
    for kind, label in LINK_LABELS:
        url = found.get(kind)
        if not url or urlparse(url).scheme != "https":
            continue
        if kind == "homepage" and url.rstrip("/") == source.rstrip("/"):
            continue
        links.append(f'<a href="{_e(url)}" rel="noopener">{label}</a>')
    return "".join(links)


def facts_markup(entry):
    facts = []
    if entry.get("released"):
        facts.append(f'<span class="badge">Released {time_markup(entry["released"], "date")}</span>')
    facts.append(license_markup(entry.get("license")))
    return "".join(facts)


def write_app_icon(site, entry, meta):
    """Writes the app's icon as a PNG, so SVG content from a bundle is never served from the Pond."""
    if not meta.icon:
        return None
    icons = Path(site) / "icons"
    icons.mkdir(exist_ok=True)
    name = f"icons/{entry['id']}.png"
    kind = images.sniff(meta.icon)
    if kind == "png":
        (Path(site) / name).write_bytes(meta.icon)
    elif kind == "svg":
        images.render_png(images._square_svg(images.Image(meta.icon, "svg", entry["id"]), 128),
                          Path(site) / name, 128, 128)
    else:
        return None
    return name


def social_tags(pond, base_url, social_name):
    """Open Graph and Twitter tags, so a shared link shows a card. Without a social image
    the card uses the Pond's icon, which apps show small beside the text."""
    image = base_url + (social_name or images.ICON)
    tags = [
        ("property", "og:type", "website"),
        ("property", "og:site_name", pond.title),
        ("property", "og:title", pond.title),
        ("property", "og:url", base_url),
        ("property", "og:image", image),
        ("property", "og:image:alt", pond.title),
        ("name", "twitter:card", "summary_large_image" if social_name else "summary"),
    ]
    if pond.subtitle:
        tags[3:3] = [("name", "description", pond.subtitle), ("property", "og:description", pond.subtitle)]
    return "\n".join(f'<meta {kind}="{key}" content="{_e(value)}">' for kind, key, value in tags)


def favicon_links(has_svg):
    links = []
    if has_svg:
        links.append('<link rel="icon" type="image/svg+xml" href="favicon.svg">')
    links.append(f'<link rel="icon" type="image/png" sizes="32x32" href="{images.FAVICON}">')
    links.append(f'<link rel="apple-touch-icon" href="{images.TOUCH_ICON}">')
    return "\n".join(links)


def logo_markup(logo_name, dark_name):
    """The logo; with a dark one, both, and the page's CSS shows the one for the current appearance.
    A <picture> could only follow the system's appearance, not the page's toggle."""
    if not dark_name:
        return f'<img src="{_e(logo_name)}" alt="">'
    return (f'<img class="logo-light" src="{_e(logo_name)}" alt="">'
            f'<img class="logo-dark" src="{_e(dark_name)}" alt="">')


# Monitor, sun and moon.
MODE_ICONS = {
    "system": '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
    "light": ('<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4'
              'M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>'),
    "dark": '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/>',
}


def mode_picker(default):
    """System, light and dark buttons; default is pressed until the page script runs."""
    buttons = []
    for mode in config.MODES:
        buttons.append(
            f'<button type="button" data-mode-choice="{mode}" aria-pressed="{str(mode == default).lower()}" '
            f'title="{mode.capitalize()}"><svg viewBox="0 0 24 24" aria-hidden="true" fill="none" '
            f'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            f'{MODE_ICONS[mode]}</svg><span class="visually-hidden">{mode.capitalize()}</span></button>')
    return f'<div class="toggle mode-picker" role="group" aria-label="Appearance">{"".join(buttons)}</div>'


def arch_picker(arches):
    """All, then each architecture; none when the Pond publishes only one."""
    if len(arches) < 2:
        return ""
    buttons = ['<button type="button" data-arch="" aria-pressed="true">All</button>']
    buttons += [f'<button type="button" data-arch="{_e(arch)}" aria-pressed="false">{_e(arch)}</button>'
                for arch in arches]
    return f'<div class="toggle arch-picker" role="group" aria-label="Show apps for">{"".join(buttons)}</div>'



def _released_key(entry):
    # A date without a time, from metainfo, counts as the start of that day in UTC.
    value = entry.get("released") or ""
    return value + "T00:00:00Z" if len(value) == 10 else value


def ordered(entries, order):
    """entries in the order pond.order names: listed, name, newest or app-id."""
    by_name = lambda e: ((e.get("name") or e["id"]).casefold(), e["id"].casefold())
    if order == "name":
        return sorted(entries, key=by_name)
    if order == "app-id":
        return sorted(entries, key=lambda e: e["id"].casefold())
    if order == "newest":
        # Newest first; apps with no known date after them, alphabetically.
        dated = sorted((e for e in entries if e.get("released")), key=by_name)
        dated = sorted(dated, key=_released_key, reverse=True)
        return dated + sorted((e for e in entries if not e.get("released")), key=by_name)
    return list(entries)


def write(site, pond, base_url, source_url, entries, logo_name, dark_name, has_svg_favicon, state,
          custom_css=False, updated=None, social_name=None):
    """entries: dicts with id, name, summary, version, released, license, url, icon.

    updated is the publish time, shown on the page; it is not part of state.
    social_name is the shared-link image in the site, or None to offer the icon.
    """
    # The page and apps.json both follow pond.order.
    entries = ordered(entries, pond.order)
    cards = []
    for entry in entries:
        icon = (f'<img src="{_e(entry["icon"])}" alt="">' if entry["icon"]
                else _e(entry["name"][:1].upper()))
        # A space, not a margin, before the version, so a version wrapped under the name is not indented.
        version = f' <small>{_e(entry["version"])}</small>' if entry["version"] else ""
        cards.append(APP.format(
            icon=icon, name=_e(entry["name"]), version=version, arches=_e(" ".join(entry.get("arches") or ())),
            summary=_e(entry["summary"] or "No description yet."), facts=facts_markup(entry),
            remote=_e(pond.remote), app_id=_e(entry["id"]), links=links_markup(entry),
            # GNOME Software 48+ and KDE Discover 6.5+ open flatpak+https: links, as Flathub's button does.
            open_url=_e(f"flatpak+{base_url}{entry['id']}.flatpakref"), chevron=CHEVRON, copy=COPY_BUTTON
            if "github.com" in (entry["url"] or "") else ""))
    source = f'<a href="{_e(source_url)}">{GITHUB_MARK}Source</a>' if source_url else ""
    light, dark = theme.palettes(pond.theme)
    page = PAGE.format(
        custom_css='<link rel="stylesheet" href="custom.css">' if custom_css else "",
        light=theme.css_variables(light),
        dark=theme.css_variables(dark),
        title=_e(pond.title),
        subtitle=f"<p>{_e(pond.subtitle)}</p>" if pond.subtitle else "",
        updated=f'Updated {time_markup(updated, "datetime")} · ' if updated else "",
        favicons=favicon_links(has_svg_favicon),
        social=social_tags(pond, base_url, social_name),
        logo=logo_markup(logo_name, dark_name),
        source=source,
        mode_attr="" if pond.mode == "system" else f' data-mode="{pond.mode}"',
        mode_picker=mode_picker(pond.mode),
        arch_picker=arch_picker(pond.arches) if cards else "",
        remote=_e(pond.remote),
        base_url=_e(base_url), copy=COPY_BUTTON,
        apps="\n".join(cards) or "<p>No apps yet.</p>",
    )
    Path(site, "index.html").write_text(page)
    public = [{k: e.get(k) for k in ("id", "name", "summary", "version", "released", "license", "license_source", "links",
                                     "url", "icon", "arches")}
              for e in entries]
    Path(site, STATE_FILE).write_text(json.dumps({"frogpak": 1, "updated": updated, "apps": public, "state": state},
                                                 indent=2) + "\n")
