"""Finds each app's latest release and the bundle for each architecture, and downloads them."""
import fnmatch
import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from . import archives, log, sources


@dataclass
class AppState:
    app: object
    source: object = None
    release: object = None
    # (arch, asset) pairs; arch is None when the pattern has no {arch} and the
    # architecture is read from the bundle on import.
    assets: list = field(default_factory=list)
    problem: str | None = None


def pattern_for(app, arch):
    return app.assets.format(app_id=app.id, name=app.name, arch=arch)


def match_assets(app, release, arches):
    """(arch, asset) pairs to fetch, warning about missing and ambiguous matches."""
    if "{arch}" not in app.assets:
        pattern = pattern_for(app, "")
        matches = [a for a in release.assets if fnmatch.fnmatchcase(a.name, pattern)]
        if not matches:
            log.notice(f"{app.id}: no asset in {release.tag} matches {pattern}")
        return [(None, a) for a in sorted(matches, key=lambda a: a.name)]
    found = []
    for arch in arches:
        pattern = pattern_for(app, arch)
        matches = [a for a in release.assets if fnmatch.fnmatchcase(a.name, pattern)]
        if len(matches) == 1:
            found.append((arch, matches[0]))
        elif matches:
            names = ", ".join(a.name for a in matches)
            log.warning(f"{app.id}: {len(matches)} assets in {release.tag} match {pattern} ({names}); {arch} skipped")
        else:
            log.notice(f"{app.id}: no asset in {release.tag} matches {pattern}; no {arch} build")
    return found


def survey(config):
    """Looks up every app. Network failures raise; per-app problems are recorded and skipped."""
    states = []
    for app in config.apps:
        state = AppState(app)
        states.append(state)
        try:
            state.source = sources.resolve(app.repo, app.forge)
            state.release = state.source.latest_release()
        except sources.SourceError as error:
            state.problem = str(error)
            log.warning(f"{app.id}: {error}; skipped")
            continue
        if state.release is None:
            state.problem = "no published release"
            log.warning(f"{app.id}: {app.repo} has no published release; skipped")
            continue
        state.assets = match_assets(app, state.release, config.pond.arches)
        if not state.assets:
            state.problem = "no matching assets"
    return states


def fingerprint(config, states, engine_version):
    """What a publish depends on. A difference from the published copy means the Pond is out of date."""
    config_text = config.path.read_bytes() if config.path and config.path.exists() else b""
    return {
        "engine": engine_version,
        "config": hashlib.sha256(config_text).hexdigest(),
        "apps": {
            s.app.id: {
                "repo": s.app.repo,
                "tag": s.release.tag if s.release else None,
                "assets": sorted([arch or "", a.name, a.size, a.id] for arch, a in s.assets),
            }
            for s in states
        },
    }


def download(states, dest):
    """Downloads every matched asset; returns (state, arch, path) for each."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    bundles = []
    for state in states:
        for number, (arch, asset) in enumerate(state.assets):
            stem = f"{state.app.id}-{arch or number}"
            path = dest / f"{stem}.download"
            log.info(f"Downloading {asset.name} for {state.app.id}")
            state.source.download(asset, path)
            if archives.is_zip(path):
                found = archives.extract_bundles(path, dest, stem)
                path.unlink()
                bundles.extend((state, arch, bundle) for bundle in found)
            else:
                bundle = path.with_suffix(".flatpak")
                path.rename(bundle)
                bundles.append((state, arch, bundle))
    return bundles
