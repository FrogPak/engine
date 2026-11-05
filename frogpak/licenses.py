"""Chooses the license shown on each app's card, and links its SPDX IDs."""
import re
from urllib.parse import urlparse

from . import log

# license: values that pick a source rather than naming a license.
KEYWORDS = {"auto": "auto", "forge": "forge", "repo": "forge", "meta": "meta", "metainfo": "meta"}
SOURCE_NAMES = {"forge": "forge", "meta": "metainfo", "config": "frogpak.yml"}
# What forges report when a repository has a license they cannot identify.
UNKNOWN = {"NOASSERTION", "NONE", "OTHER"}
OPERATORS = {"AND", "OR", "WITH"}
SPDX_URL = "https://spdx.org/licenses/{}.html"
TOKEN_RE = re.compile(r"\(|\)|[^\s()]+")
ID_RE = re.compile(r"^[A-Za-z0-9.-]+\+?$")
# GNU licenses come in -only and -or-later forms. The old bare form (GPL-3.0) is what
# forges report, since a LICENSE file does not say which was meant.
GNU_RE = re.compile(r"^(AGPL|GPL|LGPL|GFDL)-(\d(?:\.\d)?)(\+|-ONLY|-OR-LATER)?$")
MAX_LENGTH = 200


def setting(value):
    """The mode for a license: value: auto, forge, meta, or the license itself."""
    if value is None:
        return "auto"
    return KEYWORDS.get(value.strip().lower(), value.strip())


def clean(expression):
    """One line of license text, or None for nothing or a forge's 'cannot tell'."""
    text = " ".join((expression or "").split())
    if not text or text.upper() in UNKNOWN or len(text) > MAX_LENGTH:
        return None
    return text


def _terms(expression):
    terms = []
    for token in TOKEN_RE.findall(expression):
        upper = token.upper()
        if upper in OPERATORS or token in "()":
            terms.append(upper)
            continue
        gnu = GNU_RE.match(upper)
        if gnu:
            family, version, suffix = gnu.groups()
            if "." not in version:
                version += ".0"
            terms.append((family, version, {"+": "or-later", "-OR-LATER": "or-later",
                                            "-ONLY": "only", None: None}[suffix]))
        else:
            terms.append(upper)
    return terms


def _bare(expression):
    return sum(1 for t in _terms(expression) if isinstance(t, tuple) and t[2] is None)


def equivalent(a, b):
    """Same license, ignoring case, GNU spelling (GPL-3.0+ is GPL-3.0-or-later),
    and the bare GNU form a forge reports, which matches either variant."""
    ta, tb = _terms(a), _terms(b)
    if len(ta) != len(tb):
        return False
    for x, y in zip(ta, tb):
        if isinstance(x, tuple) and isinstance(y, tuple):
            if x[:2] != y[:2] or (x[2] and y[2] and x[2] != y[2]):
                return False
        elif x != y:
            return False
    return True


def resolve(app_id, value, forge, meta):
    """(license, source) for one app, where source is forge, meta or config.

    auto: the forge, then the metainfo. forge or meta: only that one. A license
    written in frogpak.yml is the last fallback, after both.
    """
    mode = setting(value)
    forge, meta = clean(forge), clean(meta)
    if mode in ("forge", "meta"):
        found = forge if mode == "forge" else meta
        if not found:
            log.warning(f"{app_id}: license is set to {value}, but the {SOURCE_NAMES[mode]} "
                        f"states no license; none is shown")
        return found, (mode if found else None)

    winner, source = (forge, "forge") if forge else (meta, "meta") if meta else (None, None)
    if forge and meta:
        if not equivalent(forge, meta):
            log.warning(f"{app_id}: the forge reports license {forge}, but the metainfo says {meta}; "
                        f"showing {forge}. Set license: meta to show the metainfo's instead.")
        elif _bare(meta) < _bare(forge):
            # The same license, stated more precisely.
            winner, source = meta, "meta"

    if mode != "auto":
        configured = clean(mode)
        if winner and configured and not equivalent(configured, winner):
            log.warning(f"{app_id}: license: {configured} in frogpak.yml differs from {winner} "
                        f"from the {SOURCE_NAMES[source]}; showing {winner}")
        if not winner:
            return configured, "config"
    return winner, source


def parts(expression):
    """(text, url) pieces for showing a license, url None for operators and unknown IDs."""
    pieces = []
    for token in TOKEN_RE.findall(expression or ""):
        if token.upper() in OPERATORS or token in "()":
            pieces.append((token, None))
        elif token.startswith(("LicenseRef-", "DocumentRef-")):
            # AppStream writes a proprietary license as LicenseRef-proprietary=https://...
            name, _, url = token.partition("=")
            pieces.append((name, url if urlparse(url).scheme in ("http", "https") else None))
        elif ID_RE.match(token):
            pieces.append((token, SPDX_URL.format(token)))
        else:
            pieces.append((token, None))
    return pieces
