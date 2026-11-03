"""Pulls Flatpak bundles out of zip files attached to releases."""
import zipfile
from pathlib import Path

from . import log

MAX_MEMBER = 2 * 1024 ** 3
MAX_TOTAL = 4 * 1024 ** 3
CHUNK = 1024 * 1024


class _TooLarge(Exception):
    pass


def is_zip(path):
    with open(path, "rb") as file:
        if file.read(4) != b"PK\x03\x04":
            return False
    return zipfile.is_zipfile(path)


def extract_bundles(path, dest, stem, max_member=MAX_MEMBER, max_total=MAX_TOTAL):
    """Writes each .flatpak in the zip to dest as <stem>-<n>.flatpak; returns their paths.

    Member names are never used as paths, so a zip cannot write outside dest. Sizes are
    counted while copying, because a zip's declared sizes can be false.
    """
    dest = Path(dest)
    written, total = [], 0
    try:
        archive = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError) as error:
        log.warning(f"{Path(path).name}: not a readable zip ({error}); skipped")
        return []
    with archive:
        for info in archive.infolist():
            if info.is_dir() or not info.filename.lower().endswith(".flatpak"):
                continue
            if info.flag_bits & 0x1:
                log.warning(f"{Path(path).name}: {info.filename} is encrypted; skipped")
                continue
            target = dest / f"{stem}-{len(written)}.flatpak"
            size = 0
            try:
                with archive.open(info) as source, open(target, "wb") as out:
                    while chunk := source.read(CHUNK):
                        size += len(chunk)
                        total += len(chunk)
                        if size > max_member or total > max_total:
                            raise _TooLarge
                        out.write(chunk)
            except _TooLarge:
                target.unlink(missing_ok=True)
                log.warning(f"{Path(path).name}: {info.filename} is too large to extract; skipped")
                if total > max_total:
                    break
                continue
            except (zipfile.BadZipFile, OSError, EOFError) as error:
                target.unlink(missing_ok=True)
                log.warning(f"{Path(path).name}: {info.filename} could not be extracted ({error}); skipped")
                continue
            written.append(target)
    if not written:
        log.warning(f"{Path(path).name}: contains no .flatpak bundle")
    return written
