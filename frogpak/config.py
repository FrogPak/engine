"""Loads and validates a pond's frogpak.yml."""
import re
import string
from dataclasses import dataclass, field
from pathlib import Path

import yaml

DEFAULT_ARCHES = ("x86_64", "aarch64")
DEFAULT_ASSETS = "{app_id}-{arch}.flatpak"
FORGES = ("github", "forgejo", "gitea", "gitlab")
PLACEHOLDERS = {"app_id", "name", "arch"}

POND_KEYS = {"title", "subtitle", "remote", "arches", "logo", "logo-dark", "favicon", "theme", "css"}
THEME_KEYS = ("accent", "accent-dark", "background", "background-dark")
APP_KEYS = {"repo", "assets", "forge"}

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

    @property
    def name(self):
        return self.id.rsplit(".", 1)[-1]


@dataclass(frozen=True)
class Pond:
    title: str
    remote: str
    subtitle: str = ""
    arches: tuple = DEFAULT_ARCHES
    logo: str | None = None
    logo_dark: str | None = None
    favicon: str | None = None
    theme: dict = field(default_factory=dict)
    css: str | None = None


@dataclass(frozen=True)
class Config:
    pond: Pond
    apps: tuple = field(default_factory=tuple)
    path: Path | None = None


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


def parse(text, path="frogpak.yml"):
    problems = []
    try:
        data = yaml.load(text, Loader=_UniqueKeyLoader)
    except yaml.YAMLError as error:
        raise ConfigError(path, [f"not valid YAML: {error}"]) from None
    if not isinstance(data, dict):
        raise ConfigError(path, ["the file must contain the 'pond' and 'apps' sections"])
    _unknown(data, {"pond", "apps"}, "", problems)

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
    for key in ("logo", "logo-dark", "favicon", "css"):
        images[key] = _string(pond_data.get(key), f"pond.{key}", problems)

    theme = {}
    raw_theme = _raw_theme(text)
    theme_data = pond_data.get("theme")
    if theme_data is not None and not isinstance(theme_data, dict):
        problems.append("pond.theme must be a mapping of colors")
        theme_data = None
    for key, value in (theme_data or {}).items():
        where = f"pond.theme.{key}"
        if key not in THEME_KEYS:
            problems.append(f"unknown key {where} (allowed: {', '.join(THEME_KEYS)})")
        elif value is None:
            # YAML reads an unquoted #rrggbb as a comment, leaving the key empty.
            problems.append(f'{where} is empty; drop the # or use quotes, for example {key}: 26a269')
        elif not isinstance(raw_theme.get(key), str) or not COLOR_RE.match(raw_theme[key].strip()):
            problems.append(f"{where} must be a hex color such as 26a269; got {raw_theme.get(key, value)!r}")
        else:
            theme[key] = "#" + raw_theme[key].strip().lstrip("#").lower()

    apps_data = data.get("apps")
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
        if repo:
            apps.append(App(app_id, repo, assets, forge))

    if problems:
        raise ConfigError(path, problems)
    pond = Pond(title=title, remote=remote, subtitle=subtitle, arches=tuple(clean_arches),
              logo=images["logo"], logo_dark=images["logo-dark"], favicon=images["favicon"],
              theme=theme, css=images["css"])
    return Config(pond=pond, apps=tuple(apps), path=Path(path))


def load(path):
    path = Path(path)
    try:
        text = path.read_text()
    except OSError as error:
        raise ConfigError(path, [f"cannot read the file: {error.strerror}"]) from None
    return parse(text, path)
