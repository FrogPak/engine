# Changelog

## 1.1.1

- App cards have an Install button that opens the app in the visitor's software center, through a `flatpak+https:` link to its `.flatpakref` (GNOME Software 48 and KDE Discover 6.5 or later). Its menu holds the `.flatpakref` download and the terminal command, which used to be on the card.
- App cards link to the app's website, issue tracker and donation page when its metainfo lists them as `https:` `<url>`s of type `homepage`, `bugtracker` and `donation`. A website that is the repository is left out, since Source already links there.
- The last-published time moved from a badge under the subtitle to the page footer, as plain text.
- Copy buttons are icons, and select the command when the browser blocks the clipboard.
- `apps.json` lists each app's `links`.
- Every Pond republishes once after upgrading, to add the Install buttons and links.

## 1.1.0

- The landing page shows when it was last published, in each visitor's time zone. `apps.json` has the same time as `updated`; it is not part of the state `poll` compares, so it never causes a republish by itself.
- App cards show the date the release was published, from the forge, or from the metainfo's newest `<release>` when the forge does not say.
- App cards show the app's license, with SPDX IDs linked to spdx.org: from the forge, then the metainfo's `<project_license>`. A new `license` app setting picks `forge` or `meta` only, or gives a license to show when neither states one. The publish warns when the sources disagree, or when the configured license differs from the one shown.
- `apps.json` lists each app's `released`, `license` and `license_source`.
- Every Pond republishes once after upgrading, to add the dates and licenses.

## 1.0.2

- The engine reports its real version. 1.0.0 and 1.0.1 reported 0.1.0, so Ponds did not notice those upgrades until an app changed; every Pond republishes once after upgrading to 1.0.2.
- The documentation site at frogpak.org rebuilds when `README.md` or `docs/` change.

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
