# Configuration reference

A Pond is configured by `pond.yml` at the root of its repository. Unknown or misspelt keys are errors, and every problem in the file is reported at once.

Before 1.1.2 the file was called `frogpak.yml`. A Pond with only `frogpak.yml` still works, with a warning in each run until it is renamed; if both files exist, `pond.yml` is used and `frogpak.yml` is ignored, with a warning. `frogpak.yml` is read until FrogPak 2.0. To use another file, set the workflow's `config` input.

```yaml
pond:
  title: Alex's Apps
  subtitle: Apps by Alex
  remote: alex
  arches: [x86_64, aarch64]
  logo-square: assets/logo-square.svg
  logo-wide: assets/logo-wide.svg
  logo-wide-dark: assets/logo-wide-dark.svg
  theme:
    accent: 1c7a4f
    background: f6f5f4

apps:
  org.example.Notes:
    repo: alex/notes
  org.example.Paint:
    repo: someone/paint
    assets: "paint-{arch}.flatpak"
    license: GPL-3.0-or-later
```

## Pond

| Key | Required | Meaning |
| --- | --- | --- |
| `title` | yes | Name shown on the landing page and in software centers |
| `subtitle` | no | One line under the title |
| `remote` | yes | Name people use for the remote: lowercase letters, digits and hyphens |
| `arches` | no | Architectures to publish; default `[x86_64, aarch64]` |
| `logo-square` | recommended | Square logo: the browser tab, the remote's icon and the badge button, and the landing page header when there is no wide logo. See [Logos](#logos-and-favicon) |
| `logo-square-dark` | no | The square logo for dark mode |
| `logo-wide` | no | A logo with the Pond's name in it; shown in place of the title on the landing page |
| `logo-wide-dark` | no | The wide logo for dark mode |
| `favicon` | no | Overrides the browser tab's icon only |
| `theme` | no | Colors, and whether the page starts in light or dark mode; see [Theme](#theme) |
| `css` | no | Your own stylesheet, a repository path or `https://` URL, loaded after FrogPak's styles |
| `social-image` | no | Image shown when the page's link is shared; default: the repository's social preview image. See [Shared links](#shared-links) |
| `order` | no | How the landing page lists apps: `listed` (default), `name`, `newest` or `app-id`. See [App order](#app-order) |

Apps can also be listed in other files; see [Included files](#included-files).

YAML guesses types for unquoted text: `no` becomes false and `1.10` becomes the number 1.1. FrogPak reports these instead of guessing along; put such values in quotes.

## apps

Each key is an app ID, such as `org.example.Notes`. Under it:

| Key | Required | Meaning |
| --- | --- | --- |
| `repo` | yes | Where the releases are: `owner/repo` on GitHub, or a full `https://` address on GitHub, Codeberg, Forgejo or Gitea |
| `assets` | no | Pattern for the release files; default `{app_id}-{arch}.flatpak` |
| `forge` | no | `github`, `forgejo`, `gitea` or `gitlab`, for a self-hosted forge FrogPak cannot recognize |
| `license` | no | Which license to show on the app's card; default `auto`. See [Licenses](#licenses) |

The Pond publishes each app's newest release that is not a pre-release. Apps that cannot be published, such as one with no release or no matching files, are skipped with a warning and the rest are published.

Each app's card shows its version, the date its release was published, and its license. It links to the app's repository, and to its website, bug tracker and donation page when its metainfo lists them (`<url type="homepage">`, `bugtracker` and `donation`, `https:` only); an app without one has no link for it. When the Pond publishes more than one architecture, buttons beside the Apps heading show only the apps available for one of them; each visitor's choice is remembered. The page's footer shows when it was last published, in each visitor's own time zone; a Pond only republishes when something changes, so that is when the page last changed, not when it was last checked.

### Licenses

The license on a card comes from the app's own sources first. The Pond's maintainer is not necessarily the app's author, so a license written in `pond.yml` is only the last fallback.

| `license` | Card shows |
| --- | --- |
| `auto` (default) | The license the forge detects in the repository; if it cannot tell, the `<project_license>` in the bundle's metainfo |
| `forge` or `repo` | Only the forge's |
| `meta` or `metainfo` | Only the metainfo's |
| An SPDX license, such as `GPL-3.0-or-later` | As `auto`; this license only when neither source states one |

- GitHub detects the license from the repository's LICENSE file. Codeberg and Gitea report it on newer versions; when one detects several license files, they are not used, since they do not say whether both apply.
- A forge that cannot identify the license, such as GitHub's `NOASSERTION`, counts as stating none.
- When the forge and the metainfo name the same license and the metainfo is more precise, the metainfo's is shown. Forges report GNU licenses as `GPL-3.0`, since a LICENSE file does not say whether `-only` or `-or-later` was meant.
- The publish warns when the forge and the metainfo disagree, and when a license in `pond.yml` differs from the one shown. `forge` or `meta` settles a disagreement without a warning.
- With no license from any source, the card says *License not stated*.
- SPDX IDs on the card link to their pages on spdx.org.

### Asset patterns

`assets` matches file names in the release. It may contain `{arch}`, `{app_id}` and `{name}` (the last part of the app ID, `Notes` in `org.example.Notes`), and may use `*` as a wildcard.

| Release files | `assets` |
| --- | --- |
| `org.example.Notes-x86_64.flatpak` | default, no setting needed |
| `Notes-x86_64-latest.flatpak` | `"{name}-{arch}-latest.flatpak"` |
| `notes-1.4.0-x86_64.flatpak` | `"notes-*-{arch}.flatpak"` |
| `org.example.Notes.flatpak` (one architecture, not in the name) | `"{app_id}.flatpak"` |
| `notes-flatpak.zip` (bundles inside a zip) | `"notes-flatpak.zip"` |

With `{arch}`, exactly one file must match per architecture. A missing architecture is noted and skipped; several matches skip that architecture with a warning.

Without `{arch}`, every matching file is used, and each one's architecture is read from the bundle itself. Architectures not in `arches`, and repeats, are skipped.

A matching file that is a zip is opened, and every `.flatpak` inside it is used, wherever it sits in the zip. Other files in the zip are ignored. Bundles larger than 2 GiB, or zips holding more than 4 GiB of bundles, are skipped.

Every bundle is checked before publishing: one that contains a different app or architecture than its entry says is skipped.

### Other forges

Apps released on Codeberg, Forgejo or Gitea work like GitHub ones; give the full repository address:

```yaml
apps:
  org.example.Notes:
    repo: https://codeberg.org/alex/notes
  org.example.Paint:
    repo: https://git.example.org/alex/paint
    forge: forgejo
```

Codeberg is recognized from its address. For a self-hosted Forgejo or Gitea, add `forge: forgejo` or `forge: gitea`; an instance served under a path, such as `https://example.org/git/`, works too. Only public repositories are supported.

GitLab is planned; until then, a GitLab `repo` is reported as not supported yet.

## Included files

`include` lists more files of apps, so a large Pond can split its list, for example one file per developer:

```yaml
include:
  - apps/alex.yml
  - apps/sam.yml

apps:
  org.example.Notes:
    repo: alex/notes
```

Each included file holds only an `apps:` section, written as in `pond.yml`:

```yaml
apps:
  org.example.Paint:
    repo: sam/paint
    assets: "paint-{arch}.flatpak"
```

- Paths are relative to the repository root and must stay inside it. Only files in the repository can be included.
- Apps are listed in `pond.yml`'s order first, then each file's, in the order of `include`. The `order` setting can sort them differently.
- An app ID listed more than once keeps its first listing, and the publish warns about the others.
- A mistake in an included file is an error naming that file, like one in `pond.yml`. A file that does not exist is skipped with a warning, and the rest are published.
- Editing an included file republishes the Pond at the next check, as editing `pond.yml` does.

## Theme

```yaml
  theme:
    mode: system
    accent: 1c7a4f
    accent-dark: 8ff0a4
    background: f6f5f4
    background-dark: "#1d1d1d"
```

`mode` is how the page looks until a visitor chooses: `system` (default) follows the visitor's system, while `light` or `dark` start the page in that mode. Buttons at the top of the page switch between system, light and dark, and each visitor's choice is remembered.

The four colors are optional hex colors, 3 or 6 digits. Write them without `#`, or with `#` inside quotes: YAML reads an unquoted `#1c7a4f` as a comment, and FrogPak reports that.

- `accent` colors links, buttons and the selected tab; `background` is the page color.
- The `-dark` variants apply when the page is in dark mode. Left out, they are derived from the light colors.
- Text, card, border and code-block colors are derived from the background.
- Derived colors are adjusted until text is readable. Colors you set are used as given; if one is hard to read, the publish warns and suggests a nearby color that passes.
- Readable means the accent has at least 4.5:1 contrast against the page and cards, where links and text use it, and 3:1 against code blocks, where it only colors the copy button's icon. These are the WCAG levels for text and for icons. The default accents, GNOME's blue, pass both.

## Custom stylesheet

`css` adds a stylesheet after FrogPak's own, so its rules win. Use it for anything the theme cannot do. The page's HTML can change between FrogPak versions, so a custom stylesheet may need updating when you upgrade; the theme colors are the stable way to restyle.

Rules for dark mode should follow the page's mode, not only the system's, so that they also apply when a visitor picks dark mode on a light system, and not when they pick light mode on a dark one:

```css
:root[data-mode="dark"] .card { border-width: 2px; }
@media (prefers-color-scheme: dark) {
  :root:not([data-mode="light"]) .card { border-width: 2px; }
}
```

## Logos and favicon

A Pond has up to two logos, each with an optional version for dark mode:

- **`logo-square`**, recommended, is the Pond's icon: the browser tab, the icon software centers show for the remote, and the badge button. Without a wide logo it is also the landing page's logo, next to the title. A publish warns when it is further from square than 1.25:1.
- **`logo-wide`** is for a logo that already contains the Pond's name, such as a wordmark. It replaces the landing page's logo and title, so the name is not shown twice; the title stays in the page for screen readers and search engines. Without `logo-square`, the wide logo is shrunk to a square for the icons, with a warning; set `logo-square` to fix it.
- **`logo-square-dark`** and **`logo-wide-dark`** are used when the page is in dark mode, and for the dark badge button.
- **`favicon`** overrides only the icon browsers show, in the tab and when the page is added to a phone's home screen.

| Set | Landing page | Browser tab, remote's icon | Badge button |
| --- | --- | --- | --- |
| `logo-square` and `logo-wide` | wide logo | square logo | square logo |
| `logo-square` only | square logo and title | square logo | square logo |
| `logo-wide` only | wide logo | wide logo, shrunk (warning) | wide logo, shrunk |
| neither | FrogPak logo and title | FrogPak logo | FrogPak logo |

`favicon`, when set, replaces the browser tab's icon in every row.

All of them take a path inside the repository or an `https://` URL. SVG and PNG are accepted; SVG is preferred. Logos are scaled, never stretched.

Without the keys, FrogPak looks at the repository root for `logo-square.svg`, `logo-square-dark.svg`, `logo-wide.svg` and `logo-wide-dark.svg`, and the same names ending in `.png`.

Before 1.2.0 the keys were `logo` and `logo-dark`, and the files `logo.svg` and `logo-dark.svg`. They still work as `logo-square` and `logo-square-dark`, with a notice in each run, until FrogPak 2.0. Setting both an old key and its new one is an error.
- URLs are fetched at every publish. If one cannot be fetched, the publish continues with the default and a warning. SVGs from URLs are published as PNG images.
- Changing a logo, favicon or `css` file in the repository republishes the page at the next check, even when `pond.yml` itself is unchanged. A file behind a URL is not watched: a change there shows at the next publish, or use **Run workflow** with *Rebuild even if nothing changed*.

## App order

| `order` | Apps listed |
| --- | --- |
| `listed` (default) | As they appear under `apps:` |
| `name` | Alphabetically by name, ignoring case |
| `newest` | Most recent release first; apps with no known release date last, alphabetically |
| `app-id` | Alphabetically by app ID, which keeps each developer's apps together (`net.example.*`, `io.github.someone.*`) |

`apps.json` lists apps in the same order. With `newest`, a new release moves its app to the top at the next publish.

## Shared links

When someone shares the page's link in a chat app or on social media, the app shows a card with the Pond's title, subtitle and an image:

1. `social-image`, if set: a PNG or JPEG, as a repository path or `https://` URL, up to 2 MB.
2. Otherwise, on GitHub, the image uploaded under the repository's **Settings > General > Social preview**. GitHub's generated card is not used, since it describes the repository rather than the Pond.
3. Otherwise the Pond's icon, which apps show as a small thumbnail beside the text.

The image is copied into the site, so the card does not depend on GitHub's copy. Uploading a new social preview image, or changing the `social-image` file, republishes the page at the next hourly check. Apps keep their own copy of a card for a while, so an old card can take time to change. 1280 × 640 pixels suits most apps.
