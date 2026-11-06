#!/usr/bin/env python3
"""Runs a full publish offline, serving release assets from a local folder.

Usage: local_publish.py BUNDLE_DIR POND_DIR OUTPUT WORK
Each app's repo setting is taken as a name; its "release" holds every file in
BUNDLE_DIR, so asset patterns are exercised as they would be on a forge.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from frogpak import cli, sources  # noqa: E402
from frogpak.sources import Asset, Release, RepoInfo, Source  # noqa: E402


class LocalSource(Source):
    forge = "local"

    def __init__(self, name, bundle_dir):
        self.name = name
        self.bundle_dir = Path(bundle_dir)

    def info(self):
        return RepoInfo(url=f"https://example.org/{self.name}", description=f"{self.name} from a local folder",
                        license="NOASSERTION" if self.name.endswith("/no-license") else "MIT")

    def latest_release(self):
        if self.name.endswith("/no-release"):
            return None
        files = sorted(f for f in self.bundle_dir.iterdir() if f.is_file())
        assets = tuple(Asset(f.name, f.resolve().as_uri(), f.stat().st_size) for f in files)
        return Release(tag="v9.9.9", url="https://example.org/release", assets=assets,
                       published="2026-01-02T03:04:05Z")


def main():
    bundle_dir, pond_dir, output, work = sys.argv[1:5]
    sources.resolve = lambda repo, forge=None: LocalSource(repo, bundle_dir)
    cli.sources.resolve = sources.resolve
    cli.fetch.sources.resolve = sources.resolve
    # No --config: like a Pond, the folder may hold pond.yml or the older frogpak.yml.
    return cli.main(["publish", "--pond-dir", pond_dir,
                     "--base-url", "http://localhost:8765/", "--source-url", "https://example.org/pond",
                     "--output", output, "--work", work])


if __name__ == "__main__":
    sys.exit(main())
