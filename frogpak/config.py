"""Loads and validates a Pond's pond.yml."""
import hashlib
import re
import string
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import log

CONFIG_NAME = "pond.yml"
# The configuration's name before 1.1.2, still read when there is no pond.yml.
OLD_CONFIG_NAME = "frogpak.yml"

DEFAULT_ARCHES = ("x86_64", "aarch64")
DEFAULT_ASSETS = "{app_id}-{arch}.flatpak"
FORGES = ("github", "forgejo", "gitea", "gitlab")
PLACEHOLDERS = {"app_id", "name", "arch"}

POND_KEYS = {"title", "subtitle", "remote", "arches", "logo-square", "logo-square-dark", "logo-wide",
             "logo-wide-dark", "logo", "logo-dark", "favicon", "theme", "css", "social-image", "order"}
# Deprecated keys and the key each one stands in for when that key is not set.
DEPRECATED_KEYS = {"logo": "logo-square", "logo-dark": "logo-square-dark"}
# How the landing page lists apps; the first is the default.
ORDERS = ("listed", "name", "newest", "app-id")
THEME_KEYS = ("mode", "accent", "accent-dark", "background", "background-dark")
# pond.theme.mode: the landing page's appearance until a visitor picks one; the first is the default.
MODES = ("system", "light", "dark")
APP_KEYS = {"repo", "assets", "forge", "license"}
LICENSE_KEYWORDS = ("auto", "forge", "repo", "meta", "metainfo")
LICENSE_RE = re.compile(r"^[A-Za-z0-9.+:=/()_ -]+$")

REMOTE_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
ARCH_RE = re.compile(r"^[a-z0-9_]+$")
COLOR_RE = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
OWNER_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
APP_ELEMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
APP_LAST_ELEMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")


class ConfigError(Exception):
    """Every problem found in the file, reported together."""

    def __init__(self, path, problems):
        self.path = path
        self.problems = problems
        super().__init__(f"{path}:\n" + "\n".join(f"  - {p}" for p in problems))


@dataclass(frozen=True)
class App:
    id: str
    repo: str
    assets: str = DEFAULT_ASSETS
    forge: str | None = None
    # auto, forge, meta, or a license expression used when neither source states one.
    license: str = "auto"
    # The file the app is listed in, when it comes from an included file; None for pond.yml.
    source: str | None = None

    @property
    def name(self):
        return self.id.rsplit(".", 1)[-1]


@dataclass(frozen=True)
class Pond:
    title: str
    remote: str
    subtitle: str = ""
    arches: tuple = DEFAULT_ARCHES
    # The square logo: the favicon, the remote's icon and the badge button, and the header without a wide logo.
    logo_square: str | None = None
    logo_square_dark: str | None = None
    # A logo with the Pond's name in it; when set it replaces the header's logo and title.
    logo_wide: str | None = None
    logo_wide_dark: str | None = None
    # Deprecated stand-ins for logo_square and logo_square_dark.
    logo: str | None = None
    logo_dark: str | None = None
    # Overrides only the icon browsers show; the remote's icon stays the square logo.
    favicon: str | None = None
    theme: dict = field(default_factory=dict)
    css: str | None = None
    # The image for shared links; None uses the repository's social preview image.
    social_image: str | None = None
    # One of ORDERS: how the landing page lists apps.
    order: str = ORDERS[0]
    # One of MODES, from pond.theme.mode. theme holds only colors.
    mode: str = MODES[0]


@dataclass(frozen=True)
class Config:
    pond: Pond
    apps: tuple = field(default_factory=tuple)
    path: Path | None = None
    # The include: list as written; load() reads the files.
    include: tuple = field(default_factory=tuple)
    # (name, sha256 of its contents or None if unreadable) for each included file, from load().
    included: tuple = field(default_factory=tuple)


class _UniqueKeyLoader(yaml.SafeLoader):
    """SafeLoader that rejects duplicate keys; PyYAML keeps the last one silently."""


def _construct_mapping(loader, node, deep=False):
    seen = {}
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate key {key!r}", key_node.start_mark)
        seen[key] = True
    return yaml.SafeLoader.construct_mapping(loader, node, deep)


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def valid_app_id(app_id):
    """Flatpak's rules: three or more elements, a hyphen allowed only in the last."""
    if len(app_id) > 255:
        return False
    parts = app_id.split(".")
    if len(parts) < 3:
        return False
    return (all(APP_ELEMENT_RE.match(p) for p in parts[:-1])
            and bool(APP_LAST_ELEMENT_RE.match(parts[-1])))


def _string(value, where, problems, required=False):
    """YAML 1.1 turns unquoted no, on, 1.10 and similar into non-strings."""
    if value is None:
        if required:
            problems.append(f"{where} is required")
        return None
    if not isinstance(value, str):
        problems.append(f"{where} must be text; got {value!r}. Put it in quotes.")
        return None
    if not value.strip():
        problems.append(f"{where} is empty")
        return None
    return value.strip()


def _unknown(mapping, allowed, where, problems):
    for key in mapping:
        if key not in allowed:
            hint = f" (allowed: {', '.join(sorted(allowed))})"
            problems.append(f"unknown key {where}{key}{hint}")


def _raw_theme(text):
    """Theme values as written in the file.

    YAML turns unquoted 123456 into a number and 012345 into an octal one, losing the digits.
    """
    try:
        root = yaml.compose(text, Loader=_UniqueKeyLoader)
    except yaml.YAMLError:
        return {}

    def child(node, name):
        if isinstance(node, yaml.MappingNode):
            for key, value in node.value:
                if isinstance(key, yaml.ScalarNode) and key.value == name:
                    return value
        return None

    theme = child(child(root, "pond"), "theme")
    if not isinstance(theme, yaml.MappingNode):
        return {}
    return {k.value: v.value for k, v in theme.value
            if isinstance(k, yaml.ScalarNode) and isinstance(v, yaml.ScalarNode) and v.value != ""}


def parse(text, path=CONFIG_NAME):
    problems = []
    try:
        data = yaml.load(text, Loader=_UniqueKeyLoader)
    except yaml.YAMLError as error:
        raise ConfigError(path, [f"not valid YAML: {error}"]) from None
    if not isinstance(data, dict):
        raise ConfigError(path, ["the file must contain the 'pond' and 'apps' sections"])
    _unknown(data, {"pond", "apps", "include"}, "", problems)
    include = _include_list(data.get("include"), problems)

    pond_data = data.get("pond")
    if not isinstance(pond_data, dict):
        problems.append("'pond' section is missing or not a mapping")
        pond_data = {}
    _unknown(pond_data, POND_KEYS, "pond.", problems)

    title = _string(pond_data.get("title"), "pond.title", problems, required=True)
    remote = _string(pond_data.get("remote"), "pond.remote", problems, required=True)
    if remote and not REMOTE_RE.match(remote):
        problems.append(f"pond.remote {remote!r} may contain only lowercase letters, digits and hyphens")
    subtitle = _string(pond_data.get("subtitle"), "pond.subtitle", problems) or ""
    order = _string(pond_data.get("order"), "pond.order", problems) or ORDERS[0]
    if order not in ORDERS:
        problems.append(f"pond.order must be one of {', '.join(ORDERS)}; got {order!r}")
        order = ORDERS[0]

    arches = pond_data.get("arches", list(DEFAULT_ARCHES))
    if not isinstance(arches, list) or not arches:
        problems.append("pond.arches must be a list such as [x86_64, aarch64]")
        arches = list(DEFAULT_ARCHES)
    clean_arches = []
    for i, arch in enumerate(arches):
        arch = _string(arch, f"pond.arches[{i}]", problems)
        if arch and not ARCH_RE.match(arch):
            problems.append(f"pond.arches[{i}] {arch!r} is not a Flatpak architecture name")
        elif arch and arch not in clean_arches:
            clean_arches.append(arch)

    images = {}
    for key in ("logo-square", "logo-square-dark", "logo-wide", "logo-wide-dark", "logo", "logo-dark", "favicon",
                "css", "social-image"):
        images[key] = _string(pond_data.get(key), f"pond.{key}", problems)
    for old, new in DEPRECATED_KEYS.items():
        if images[old] and images[new]:
            problems.append(f"pond.{old} and pond.{new} are both set; pond.{old} is the old name, so remove it")

    theme = {}
    mode = MODES[0]
    raw_theme = _raw_theme(text)
    theme_data = pond_data.get("theme")
    if theme_data is not None and not isinstance(theme_data, dict):
        problems.append("pond.theme must be a mapping of colors")
        theme_data = None
    for key, value in (theme_data or {}).items():
        where = f"pond.theme.{key}"
        if key not in THEME_KEYS:
            problems.append(f"unknown key {where} (allowed: {', '.join(THEME_KEYS)})")
        elif key == "mode":
            given = _string(value, where, problems)
            if given and given not in MODES:
                problems.append(f"{where} must be one of {', '.join(MODES)}; got {given!r}")
            elif given:
                mode = given
        elif value is None:
            # YAML reads an unquoted #rrggbb as a comment, leaving the key empty.
            problems.append(f'{where} is empty; drop the # or use quotes, for example {key}: 26a269')
        elif not isinstance(raw_theme.get(key), str) or not COLOR_RE.match(raw_theme[key].strip()):
            problems.append(f"{where} must be a hex color such as 26a269; got {raw_theme.get(key, value)!r}")
        else:
            theme[key] = "#" + raw_theme[key].strip().lstrip("#").lower()

    apps = _parse_apps(data.get("apps"), problems)

    if problems:
        raise ConfigError(path, problems)
    pond = Pond(title=title, remote=remote, subtitle=subtitle, arches=tuple(clean_arches),
              logo_square=images["logo-square"], logo_square_dark=images["logo-square-dark"],
              logo_wide=images["logo-wide"], logo_wide_dark=images["logo-wide-dark"],
              logo=images["logo"], logo_dark=images["logo-dark"], favicon=images["favicon"],
              theme=theme, css=images["css"], social_image=images["social-image"], order=order, mode=mode)
    return Config(pond=pond, apps=tuple(apps), path=Path(path), include=include)


def _include_list(value, problems):
    """include: as a tuple of repository-relative paths."""
    if value is None:
        return ()
    if not isinstance(value, list):
        problems.append("include must be a list of files, such as [apps/alex.yml]")
        return ()
    found = []
    for i, item in enumerate(value):
        name = _string(item, f"include[{i}]", problems)
        if not name:
            continue
        if Path(name).is_absolute() or ".." in Path(name).parts:
            problems.append(f"include[{i}] {name!r} must be a path inside the repository, such as apps/alex.yml")
        elif name not in found:
            found.append(name)
    return tuple(found)


def _parse_apps(apps_data, problems, source=None):
    """The apps: section of pond.yml or of an included file."""
    if apps_data is None:
        apps_data = {}
    if not isinstance(apps_data, dict):
        problems.append("'apps' must be a mapping of app IDs to settings")
        apps_data = {}
    apps = []
    for app_id, settings in apps_data.items():
        where = f"apps.{app_id}"
        if not isinstance(app_id, str) or not valid_app_id(app_id):
            problems.append(f"{where}: {app_id!r} is not a valid Flatpak app ID")
            continue
        if not isinstance(settings, dict):
            problems.append(f"{where} must be a mapping with at least 'repo'")
            continue
        _unknown(settings, APP_KEYS, f"{where}.", problems)
        repo = _string(settings.get("repo"), f"{where}.repo", problems, required=True)
        if repo and not (OWNER_REPO_RE.match(repo) or repo.startswith("https://")):
            problems.append(f"{where}.repo must be owner/repo (GitHub) or an https:// URL")
        assets = _string(settings.get("assets"), f"{where}.assets", problems) or DEFAULT_ASSETS
        try:
            fields = {f for _, f, _, _ in string.Formatter().parse(assets) if f is not None}
        except ValueError:
            fields = {"?"}
        if fields - PLACEHOLDERS:
            problems.append(f"{where}.assets may only use the placeholders {{app_id}}, {{name}} and {{arch}}")
        if "/" in assets:
            problems.append(f"{where}.assets is a file name pattern and cannot contain '/'")
        forge = _string(settings.get("forge"), f"{where}.forge", problems)
        if forge and forge not in FORGES:
            problems.append(f"{where}.forge must be one of {', '.join(FORGES)}")
        license = _string(settings.get("license"), f"{where}.license", problems) or "auto"
        if license.lower() in LICENSE_KEYWORDS:
            license = {"repo": "forge", "metainfo": "meta"}.get(license.lower(), license.lower())
        elif len(license) > 200 or not LICENSE_RE.match(license):
            problems.append(f"{where}.license must be auto, forge, meta, or an SPDX license such as "
                            f"GPL-3.0-or-later; got {license!r}")
        if repo:
            apps.append(App(app_id, repo, assets, forge, license, source))
    return apps


def parse_included(text, name):
    """The apps in an included file, which holds only an apps: section."""
    problems = []
    try:
        data = yaml.load(text, Loader=_UniqueKeyLoader)
    except yaml.YAMLError as error:
        raise ConfigError(name, [f"not valid YAML: {error}"]) from None
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ConfigError(name, ["an included file must contain an 'apps' section"])
    _unknown(data, {"apps"}, "", problems)
    apps = _parse_apps(data.get("apps"), problems, source=name)
    if problems:
        raise ConfigError(name, problems)
    return apps


def find(path=None, root=".", warn=True):
    """The configuration file: path as given; otherwise pond.yml in root, or the older
    frogpak.yml when there is no pond.yml. warn=False keeps a second command in the same
    run from repeating the warnings."""
    if path:
        return Path(path)
    new, old = Path(root) / CONFIG_NAME, Path(root) / OLD_CONFIG_NAME
    if new.is_file():
        if old.is_file() and warn:
            log.warning(f"{OLD_CONFIG_NAME} is ignored because {CONFIG_NAME} exists. Move any settings you "
                        f"still need into {CONFIG_NAME}, then delete {OLD_CONFIG_NAME}.")
        return new
    if old.is_file():
        if warn:
            log.warning(f"{OLD_CONFIG_NAME} is the old name for the Pond configuration; rename it to "
                        f"{CONFIG_NAME}. {OLD_CONFIG_NAME} works until FrogPak 2.0.")
        return old
    return new


def load(path, warn=True):
    """The configuration, with the apps of each included file after pond.yml's own.

    An included file that cannot be read is skipped with a warning; one with mistakes is an
    error naming that file. An app ID listed twice keeps its first listing, pond.yml's first.
    warn=False keeps a second command in the same run from repeating the warnings.
    """
    path = Path(path)
    try:
        text = path.read_text()
    except OSError as error:
        raise ConfigError(path, [f"cannot read the file: {error.strerror}"]) from None
    cfg = parse(text, path)
    if not cfg.include:
        return cfg

    root = path.parent.resolve()
    apps, included = list(cfg.apps), []
    seen = {app.id: path.name for app in apps}
    for name in cfg.include:
        file = (root / name).resolve()
        try:
            if root not in file.parents:
                raise OSError(0, "it is outside the repository")
            data = file.read_bytes()
        except OSError as error:
            if warn:
                log.warning(f"include {name}: cannot be read ({error.strerror}); its apps are skipped")
            included.append((name, None))
            continue
        included.append((name, hashlib.sha256(data).hexdigest()))
        for app in parse_included(data.decode("utf-8", "replace"), name):
            if app.id in seen:
                if warn:
                    log.warning(f"{name}: {app.id} is already listed in {seen[app.id]}; this listing is skipped")
                continue
            seen[app.id] = name
            apps.append(app)
    return Config(pond=cfg.pond, apps=tuple(apps), path=cfg.path, include=cfg.include, included=tuple(included))
