"""Command line: frogpak check | poll | publish."""
import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from . import __version__, config, fetch, http, images, licenses, log, repo, site, social, sources


def _base_url(value):
    return value.rstrip("/") + "/"


def _output(name, value):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a") as out:
            out.write(f"{name}={value}\n")
    print(f"{name}={value}")


def _normalize(data):
    return json.loads(json.dumps(data))


def _now():
    """The publish time for the page. SOURCE_DATE_EPOCH fixes it, for reproducible builds."""
    epoch = os.environ.get("SOURCE_DATE_EPOCH", "")
    moment = datetime.fromtimestamp(int(epoch), timezone.utc) if epoch.isdigit() else datetime.now(timezone.utc)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def cmd_check(args):
    cfg = config.load(config.find(args.config))
    log.info(f"{cfg.path}: OK, {len(cfg.apps)} app(s)")
    for app in cfg.apps:
        try:
            sources.resolve(app.repo, app.forge)
        except sources.SourceError as error:
            log.warning(f"{app.id}: {error}")
    return 0


def cmd_poll(args):
    # check runs first in the same job and has already warned about the file's name.
    cfg = config.load(config.find(args.config, warn=False))
    # Quiet: publish warns if the image cannot be looked up, and poll runs every hour.
    image = social.identity(social.source(cfg.pond, warn=False), ".")
    current = _normalize(fetch.fingerprint(cfg, fetch.survey(cfg), __version__, image))
    url = _base_url(args.base_url) + site.STATE_FILE
    try:
        # The query string sidesteps the Pages CDN cache, which holds files for ten minutes.
        published = http.get_json(f"{url}?t={int(time.time())}").get("state")
    except http.HTTPError as error:
        log.info(f"No published state at {url} ({error.status}); publishing")
        published = None
    except (ValueError, AttributeError):
        log.warning(f"{url} is not valid FrogPak state; publishing")
        published = None
    changed = published != current
    if changed and published:
        for app_id in sorted(set(current["apps"]) | set(published.get("apps", {}))):
            if current["apps"].get(app_id) != published.get("apps", {}).get(app_id):
                log.info(f"Changed: {app_id}")
        for key in ("engine", "config"):
            if current.get(key) != published.get(key):
                log.info(f"Changed: {key}")
    _output("changed", "true" if changed else "false")
    return 0


PAGES_LIMIT = 1024 ** 3
PAGES_WARN = 0.75


def size_guard(out, bundles):
    """GitHub Pages refuses sites over 1 GB; fails before deploying so the live site stays up."""
    out = Path(out)
    # ostree's tmp/ is not deployed.
    total = sum(f.stat().st_size for f in out.rglob("*") if f.is_file() and f.relative_to(out).parts[0] != "tmp")
    if total < PAGES_LIMIT * PAGES_WARN:
        log.info(f"Site size: {total / 1024 ** 2:.0f} MB of GitHub Pages' 1 GB limit")
        return True
    per_app = {}
    for state, _, path in bundles:
        per_app[state.app.id] = per_app.get(state.app.id, 0) + path.stat().st_size
    largest = ", ".join(f"{app} {size / 1024 ** 2:.0f} MB"
                        for app, size in sorted(per_app.items(), key=lambda item: -item[1])[:5])
    message = f"site is {total / 1024 ** 2:.0f} MB of GitHub Pages' 1 GB limit; largest apps: {largest}"
    if total >= PAGES_LIMIT:
        log.error(f"Not deploying: {message}")
        return False
    log.warning(message)
    return True


def cmd_publish(args):
    cfg = config.load(config.find(args.config, args.pond_dir))
    pond = cfg.pond
    base_url = _base_url(args.base_url)
    out = Path(args.output)
    work = Path(args.work)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    work.mkdir(parents=True, exist_ok=True)

    key = repo.signing_key()
    states = fetch.survey(cfg)
    bundles = fetch.download(states, work / "bundles")

    repo.init(out)
    app_refs = {}
    for state, arch, path in bundles:
        ref = repo.import_bundle(out, key, state.app.id, arch, path, work, pond.arches,
                                 app_refs.get(state.app.id, []))
        if ref:
            app_refs.setdefault(state.app.id, []).append(ref)
    repo.update(out, key, pond.title, pond.subtitle or pond.title)

    logo, dark, favicon = images.resolve(pond, args.pond_dir)
    logo_name = images.write_logo(logo, out, "logo")
    dark_name = images.write_logo(dark, out, "logo-dark") if dark else None
    has_svg = images.write_icons(favicon, out)
    repo.write_repo_file(out, pond, base_url, key, base_url + images.ICON)

    entries = []
    for state in states:
        refs = sorted(app_refs.get(state.app.id, []))
        if not refs:
            if not state.problem:
                log.warning(f"{state.app.id}: no bundle could be published; skipped")
            continue
        meta = repo.read_metadata(out, refs[0], state.app.id)
        try:
            info = state.source.info()
        except (sources.SourceError, http.NetworkError) as error:
            log.warning(f"{state.app.id}: {error}")
            info = sources.RepoInfo(url=state.source.web, description="")
        license, license_source = licenses.resolve(state.app.id, state.app.license, info.license, meta.license,
                                                   cfg.path.name)
        entry = {
            "id": state.app.id,
            "name": meta.name or state.app.name,
            "summary": meta.summary or info.description,
            "version": meta.version or state.release.tag.removeprefix("v"),
            "released": state.release.published or meta.released,
            "license": license,
            "license_source": license_source,
            "url": info.url,
            "links": meta.links,
            "arches": sorted(r.split("/")[2] for r in refs),
        }
        entry["icon"] = site.write_app_icon(out, entry, meta)
        repo.write_ref_file(out, pond, base_url, key, state.app.id, refs[0].split("/")[3],
                            entry["name"], entry["summary"])
        entries.append(entry)

    custom_css = False
    if pond.css:
        loaded = images.read_file(pond.css, args.pond_dir, "no custom stylesheet")
        if loaded:
            (out / "custom.css").write_bytes(loaded[0])
            custom_css = True

    image_source = social.source(pond)
    social_name = social.write(out, image_source, args.pond_dir)

    fingerprint = fetch.fingerprint(cfg, states, __version__, social.identity(image_source, args.pond_dir))
    # The publish time is shown on the page but kept out of the fingerprint, so it never
    # makes a Pond look out of date by itself.
    site.write(out, pond, base_url, args.source_url, entries, logo_name, dark_name, has_svg, fingerprint,
               custom_css, updated=_now(), social_name=social_name)
    if not size_guard(out, bundles):
        return 1
    log.info(f"Published {len(entries)} of {len(cfg.apps)} app(s) to {out}")
    if cfg.apps and not entries:
        log.warning("No apps could be published")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="frogpak")
    parser.add_argument("--version", action="version", version=f"FrogPak {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    # Without --config: pond.yml, or the older frogpak.yml when there is no pond.yml.
    config_help = "the Pond configuration (default: pond.yml, or frogpak.yml)"
    check = commands.add_parser("check", help="validate the Pond configuration")
    check.add_argument("--config", help=config_help)

    poll = commands.add_parser("poll", help="report whether the published Pond is out of date")
    poll.add_argument("--config", help=config_help)
    poll.add_argument("--base-url", required=True)

    publish = commands.add_parser("publish", help="build the signed repository and site")
    publish.add_argument("--config", help=config_help)
    publish.add_argument("--base-url", required=True)
    publish.add_argument("--pond-dir", default=".")
    publish.add_argument("--source-url", default="")
    publish.add_argument("--output", required=True)
    publish.add_argument("--work", required=True)

    args = parser.parse_args(argv)
    handler = {"check": cmd_check, "poll": cmd_poll, "publish": cmd_publish}[args.command]
    try:
        return handler(args)
    except config.ConfigError as error:
        print(error, file=sys.stderr)
        log.error(f"{error.path} has {len(error.problems)} problem(s); see the log")
        return 2
    except (repo.RepoError, http.NetworkError, http.HTTPError) as error:
        log.error(str(error))
        return 1
