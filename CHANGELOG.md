# Changelog

## 1.1.6

- A new `include` setting lists more files of apps, such as one per developer. Each holds an `apps:` section like `pond.yml`'s. Editing one republishes the Pond at the next check.
- The page has system, light and dark buttons, and remembers each visitor's choice. A new `theme.mode` setting starts the page in `light` or `dark` mode instead of following the visitor's system. The dark logo and colors follow the page's mode. A custom stylesheet's `prefers-color-scheme` rules follow only the system; see [Custom stylesheet](docs/configuration.md#custom-stylesheet).
- When a Pond publishes more than one architecture, buttons beside the Apps heading show only the apps for one, and each visitor's choice is remembered. On narrow screens they go under the heading.
- On the narrowest phones, an app card's Install button goes under the app's name instead of past the card's edge, and a long name wraps between words with its version kept whole.

## 1.1.5

- A new `order` setting chooses how the landing page lists apps: `listed`, the default and the order before; `name`; `newest`, by release date; or `app-id`, which keeps each developer's apps together. `apps.json` follows the same order.

## 1.1.4

- Changing a logo, dark logo, favicon or stylesheet file republishes the page at the next check. Before, only changes to `pond.yml` and to apps' releases did, so a new logo waited for one of those or a forced rebuild. Files behind URLs are not watched.
- The accent's contrast against code blocks is checked against 3:1, the level for icons, since there it only colors the copy button's icon; the page and cards still need 4.5:1. Accents that were readable everywhere except code blocks, such as GNOME's blue, no longer warn.

## 1.1.3

- Shared links to a Pond's page show a card: the page has Open Graph and Twitter tags with the Pond's title, subtitle and an image. The image is the new `social-image` setting, or else the repository's uploaded social preview image, or else the Pond's icon. A new image republishes the page at the next hourly check.

## 1.1.2

- The reusable workflow is renamed from `pond.yml` to `publish-pond.yml`. In your Pond's `.github/workflows/publish.yml`, change `FrogPak/engine/.github/workflows/pond.yml@v1` to `FrogPak/engine/.github/workflows/publish-pond.yml@v1`. A Pond still calling `pond.yml` fails with a notice saying so, and publishes nothing until it is updated; its site stays as it was.
- The Pond configuration is now `pond.yml`, the name the workflow used to have. A Pond with only `frogpak.yml` keeps working, with a warning to rename it; when both exist, `pond.yml` is used and the publish warns that `frogpak.yml` is ignored. `frogpak.yml` is read until 2.0. The workflow's `config` input now defaults to finding the file; a Pond that sets it gets exactly that file.

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
