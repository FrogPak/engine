# Changelog

## 1.0.1

- Documentation, workflow and log text capitalize Pond as FrogPak's term for a deployment. Configuration keys, inputs and file names are unchanged.

## 1.0.0

First release.

- Reusable workflow `pond.yml`: checks each app's latest release hourly and publishes a signed Flatpak repository with a landing page to GitHub Pages when something changed.
- `frogpak.yml` configuration with strict validation: title, remote name, architectures, logos, favicon, theme colors, and apps.
- Apps from GitHub, Codeberg, Forgejo and Gitea releases. Asset patterns with or without `{arch}`, and bundles inside zip files.
- Every bundle is checked against its app ID and architecture before publishing; a bad bundle is skipped and the rest are published.
- Landing page in light and dark mode, with System/User install commands, app icons, versions and summaries from metainfo.
- Setup check that warns on scheduled runs, and keeps the hourly schedule active.
