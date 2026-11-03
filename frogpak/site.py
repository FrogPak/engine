"""Writes the landing page and apps.json into the published site."""
import html
import json
from urllib.parse import urlparse
from pathlib import Path

from . import images, theme

STATE_FILE = "apps.json"
GITHUB_MARK = (
    '<svg class="mark" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">'
    '<path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>'
    "</svg>"
)

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
{favicons}
<style>
:root {{ {light} }}
@media (prefers-color-scheme: dark) {{
  :root {{ {dark} }}
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; background: var(--bg); color: var(--fg);
  font: 16px/1.5 system-ui, -apple-system, "Cantarell", "Segoe UI", sans-serif;
}}
main {{ max-width: 44rem; margin: 0 auto; padding: 2rem 1rem 4rem; }}
h1 {{ font-size: 1.75rem; margin: 0; }}
.top {{ display: flex; align-items: center; justify-content: space-between; gap: 1rem; margin-bottom: .25rem; }}
.brand {{ display: flex; align-items: center; gap: .75rem; min-width: 0; }}
.brand img {{ height: 44px; width: auto; max-width: 10rem; object-fit: contain; flex: none; }}
.mark {{ vertical-align: -2px; margin-right: .3rem; }}
h2 {{ font-size: 1.15rem; margin: 2rem 0 .75rem; }}
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
.app h3 {{ margin: 0; font-size: 1.1rem; }}
.app h3 small {{ color: var(--muted); font-weight: normal; font-size: .85rem; margin-left: .35rem; }}
.app p {{ margin: .25rem 0 .75rem; }}
.links {{ font-size: .9rem; margin-top: .6rem; }}
.links a {{ margin-right: 1rem; }}
.cmd {{
  display: flex; align-items: flex-start; gap: .5rem; background: var(--code);
  border-radius: 8px; padding: .5rem .75rem;
}}
.cmd code {{
  flex: 1; min-width: 0; overflow-wrap: anywhere;
  font: .85rem ui-monospace, "Source Code Pro", monospace;
}}
.cmd button {{
  flex: none; font: inherit; font-size: .85rem; color: var(--accent);
  background: none; border: 1px solid var(--border); border-radius: 6px;
  padding: .15rem .6rem; cursor: pointer;
}}
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
footer {{ margin-top: 3rem; font-size: .85rem; color: var(--muted); text-align: center; }}
</style>
{custom_css}
</head>
<body>
<main>
<div class="top">
<div class="brand">{logo}<h1>{title}</h1></div>
{source}
</div>
{subtitle}

<h2>Add the repository</h2>
<div class="card">
<div class="scope-picker" role="group" aria-label="Installation">
<button type="button" data-scope="system" aria-pressed="true">System</button>
<button type="button" data-scope="user" aria-pressed="false">User</button>
</div>
<div class="cmd"><code>flatpak remote-add<span class="scope"></span> --if-not-exists {remote} {base_url}index.flatpakrepo</code><button type="button">Copy</button></div>
<p class="hint" data-for="system">For everyone on this computer. May ask for your password.</p>
<p class="hint" data-for="user" hidden>For your account only. No password needed.</p>
</div>

<h2>Apps</h2>
{apps}
<footer>Published with <a href="https://github.com/FrogPak/engine">FrogPak</a></footer>
</main>
<script>
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
let savedScope = null;
try {{ savedScope = localStorage.getItem(SCOPE_KEY); }} catch (error) {{}}
setScope(savedScope === "user" ? "user" : "system");
for (const button of document.querySelectorAll(".cmd button")) {{
  button.addEventListener("click", async () => {{
    const text = button.parentElement.querySelector("code").textContent;
    try {{ await navigator.clipboard.writeText(text); button.textContent = "Copied"; }}
    catch (error) {{ button.textContent = "Select and copy"; }}
    setTimeout(() => {{ button.textContent = "Copy"; }}, 2000);
  }});
}}
</script>
</body>
</html>
"""

APP = """<div class="card app">
<div class="icon">{icon}</div>
<div class="body">
<h3>{name}{version}</h3>
<p>{summary}</p>
<div class="cmd"><code>flatpak install<span class="scope"></span> {remote} {app_id}</code><button type="button">Copy</button></div>
<div class="links"><a href="{url}">{mark}Source</a><a href="{app_id}.flatpakref">Install file (.flatpakref)</a></div>
</div>
</div>"""


def _e(value):
    return html.escape(value or "", quote=True)


def _web(url):
    return url if urlparse(url or "").scheme in ("http", "https") else "#"


def write_app_icon(site, entry, meta):
    """Writes the app's icon as a PNG, so SVG content from a bundle is never served from the pond."""
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


def favicon_links(has_svg):
    links = []
    if has_svg:
        links.append('<link rel="icon" type="image/svg+xml" href="favicon.svg">')
    links.append(f'<link rel="icon" type="image/png" sizes="32x32" href="{images.FAVICON}">')
    links.append(f'<link rel="apple-touch-icon" href="{images.TOUCH_ICON}">')
    return "\n".join(links)


def logo_markup(logo_name, dark_name):
    img = f'<img src="{_e(logo_name)}" alt="">'
    if not dark_name:
        return img
    return (f'<picture><source srcset="{_e(dark_name)}" media="(prefers-color-scheme: dark)">'
            f"{img}</picture>")


def write(site, pond, base_url, source_url, entries, logo_name, dark_name, has_svg_favicon, state,
          custom_css=False):
    """entries: dicts with id, name, summary, version, url, icon."""
    cards = []
    for entry in entries:
        icon = (f'<img src="{_e(entry["icon"])}" alt="">' if entry["icon"]
                else _e(entry["name"][:1].upper()))
        version = f'<small>{_e(entry["version"])}</small>' if entry["version"] else ""
        cards.append(APP.format(
            icon=icon, name=_e(entry["name"]), version=version,
            summary=_e(entry["summary"] or "No description yet."),
            remote=_e(pond.remote), app_id=_e(entry["id"]), url=_e(_web(entry["url"])), mark=GITHUB_MARK
            if "github.com" in (entry["url"] or "") else ""))
    source = f'<a href="{_e(source_url)}">{GITHUB_MARK}Source</a>' if source_url else ""
    light, dark = theme.palettes(pond.theme)
    page = PAGE.format(
        custom_css='<link rel="stylesheet" href="custom.css">' if custom_css else "",
        light=theme.css_variables(light),
        dark=theme.css_variables(dark),
        title=_e(pond.title),
        subtitle=f"<p>{_e(pond.subtitle)}</p>" if pond.subtitle else "",
        favicons=favicon_links(has_svg_favicon),
        logo=logo_markup(logo_name, dark_name),
        source=source,
        remote=_e(pond.remote),
        base_url=_e(base_url),
        apps="\n".join(cards) or "<p>No apps yet.</p>",
    )
    Path(site, "index.html").write_text(page)
    public = [{k: e.get(k) for k in ("id", "name", "summary", "version", "url", "icon", "arches")}
              for e in entries]
    Path(site, STATE_FILE).write_text(json.dumps({"frogpak": 1, "apps": public, "state": state}, indent=2) + "\n")
