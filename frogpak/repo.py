"""Builds the signed OSTree repository and reads app metadata back out of it."""
import base64
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from . import log

FLATHUB_REPO = "https://dl.flathub.org/repo/flathub.flatpakrepo"
SETUP_DOCS = "https://github.com/FrogPak/engine/blob/main/docs/setup.md#signing-key"
ICON_PATHS = (
    "scalable/apps/{id}.svg",
    "512x512/apps/{id}.png",
    "256x256/apps/{id}.png",
    "128x128/apps/{id}.png",
    "64x64/apps/{id}.png",
)


class RepoError(Exception):
    pass


@dataclass
class Key:
    fingerprint: str
    homedir: str
    public_b64: str


@dataclass
class Metadata:
    name: str | None = None
    summary: str | None = None
    version: str | None = None
    icon: bytes | None = None
    icon_ext: str | None = None


def run(*args, binary=False, check=True):
    result = subprocess.run(args, capture_output=True, text=not binary)
    if check and result.returncode != 0:
        stderr = result.stderr if not binary else result.stderr.decode(errors="replace")
        raise RepoError(f"{' '.join(map(str, args[:3]))} failed: {stderr.strip()}")
    return result


def signing_key():
    homedir = os.environ.get("GNUPGHOME") or str(Path.home() / ".gnupg")
    out = run("gpg", "--homedir", homedir, "--batch", "--list-secret-keys", "--with-colons", check=False).stdout
    fingerprints = [line.split(":")[9] for line in out.splitlines() if line.startswith("fpr:")]
    if not fingerprints:
        raise RepoError(f"No signing key found. Add the GPG_PRIVATE_KEY secret; see {SETUP_DOCS}")
    fpr = fingerprints[0]
    public = run("gpg", "--homedir", homedir, "--batch", "--export", fpr, binary=True).stdout
    return Key(fpr, homedir, base64.b64encode(public).decode())


def refs(repo):
    return set(run("ostree", "refs", f"--repo={repo}").stdout.split())


def init(repo):
    run("ostree", "init", "--mode=archive", f"--repo={repo}")


def import_bundle(repo, key, app_id, arch, path, workdir, arches=(), taken=()):
    """Imports one bundle; returns its ref, or None when it holds the wrong app or arch.

    With arch None, any architecture in arches is accepted unless its ref is in taken.
    """
    # Staged in its own repo: importing straight into the Pond would let a mislabeled
    # bundle overwrite another app's ref before it could be checked.
    stage = Path(workdir) / f"stage-{app_id}-{arch}"
    shutil.rmtree(stage, ignore_errors=True)
    try:
        init(stage)
        try:
            run("flatpak", "build-import-bundle", f"--gpg-sign={key.fingerprint}",
                f"--gpg-homedir={key.homedir}", str(stage), str(path))
        except RepoError as error:
            log.warning(f"{app_id}: {path.name} could not be imported ({error}); skipped")
            return None
        found = sorted(refs(stage))
        parts = found[0].split("/") if len(found) == 1 else []
        wanted = (parts[:2] == ["app", app_id] and len(parts) == 4
                  and (parts[2] == arch if arch else parts[2] in arches))
        if not wanted:
            expected = f"app/{app_id}/{arch or '{' + ','.join(arches) + '}'}"
            log.warning(f"{app_id}: {path.name} contains {', '.join(found) or 'nothing'}, "
                        f"expected {expected}; skipped")
            return None
        if found[0] in taken:
            log.warning(f"{app_id}: {path.name} repeats {found[0]}; skipped")
            return None
        run("ostree", "pull-local", f"--repo={repo}", str(stage), found[0])
        return found[0]
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def update(repo, key, title, comment):
    run("flatpak", "build-update-repo", f"--gpg-sign={key.fingerprint}", f"--gpg-homedir={key.homedir}",
        f"--title={title}", f"--comment={comment}", "--prune", str(repo))


def _cat(repo, ref, path):
    result = run("ostree", "cat", f"--repo={repo}", ref, path, binary=True, check=False)
    return result.stdout if result.returncode == 0 else None


def _text(element):
    return " ".join("".join(element.itertext()).split()) if element is not None else None


def _untranslated(root, tag):
    for element in root.findall(tag):
        if not element.get("{http://www.w3.org/XML/1998/namespace}lang"):
            return element
    return None


def read_metadata(repo, ref, app_id):
    meta = Metadata()
    for path in (f"/files/share/metainfo/{app_id}.metainfo.xml", f"/files/share/metainfo/{app_id}.appdata.xml",
                 f"/files/share/appdata/{app_id}.appdata.xml"):
        data = _cat(repo, ref, path)
        if data is None:
            continue
        try:
            root = ET.fromstring(data)
        except ET.ParseError as error:
            log.warning(f"{app_id}: cannot parse {path}: {error}")
            break
        meta.name = _text(_untranslated(root, "name"))
        meta.summary = _text(_untranslated(root, "summary"))
        # AppStream lists releases newest first.
        release = root.find("./releases/release")
        if release is not None:
            meta.version = release.get("version")
        break
    for template in ICON_PATHS:
        path = "/export/share/icons/hicolor/" + template.format(id=app_id)
        data = _cat(repo, ref, path)
        if data:
            meta.icon, meta.icon_ext = data, Path(path).suffix
            break
    return meta


def _value(text):
    """Keyfile values must stay on one line; a newline would add keys."""
    return " ".join(str(text).split())


def write_repo_file(site, pond, base_url, key, icon_url):
    lines = [
        "[Flatpak Repo]",
        f"Title={_value(pond.title)}",
        f"Url={base_url}",
        f"Homepage={base_url}",
        f"Comment={_value(pond.subtitle or pond.title)}",
    ]
    if icon_url:
        lines.append(f"Icon={icon_url}")
    lines.append(f"GPGKey={key.public_b64}")
    (Path(site) / "index.flatpakrepo").write_text("\n".join(lines) + "\n")


def write_ref_file(site, pond, base_url, key, app_id, branch, name, summary):
    lines = [
        "[Flatpak Ref]",
        f"Title={_value(name)}",
        f"Name={app_id}",
        f"Branch={branch}",
        f"Url={base_url}",
        f"SuggestRemoteName={pond.remote}",
        "IsRuntime=false",
        f"RuntimeRepo={FLATHUB_REPO}",
    ]
    if summary:
        lines.insert(2, f"Comment={_value(summary)}")
    lines.append(f"GPGKey={key.public_b64}")
    (Path(site) / f"{app_id}.flatpakref").write_text("\n".join(lines) + "\n")
