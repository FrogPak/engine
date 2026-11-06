# Configuration reference

A Pond is configured by `pond.yml` at the root of its repository. Unknown or misspelt keys are errors, and every problem in the file is reported at once.

Before 1.1.2 the file was called `frogpak.yml`. A Pond with only `frogpak.yml` still works, with a warning in each run until it is renamed; if both files exist, `pond.yml` is used and `frogpak.yml` is ignored, with a warning. `frogpak.yml` is read until FrogPak 2.0. To use another file, set the workflow's `config` input.

```yaml
pond:
  title: Alex's Apps
  subtitle: Apps by Alex
  remote: alex
  arches: [x86_64, aarch64]
  logo: assets/logo.svg
  logo-dark: assets/logo-dark.svg
  favicon: assets/icon.svg
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
| `logo` | no | Logo for the landing page; see [Logos](#logos-and-favicon) |
| `logo-dark` | no | Logo used when the visitor's system is in dark mode |
| `favicon` | no | Square image for the browser tab and the remote's icon |
| `theme` | no | Colors; see [Theme](#theme) |
| `css` | no | Your own stylesheet, a repository path or `https://` URL, loaded after FrogPak's styles |
| `social-image` | no | Image shown when the page's link is shared; default: the repository's social preview image. See [Shared links](#shared-links) |
| `order` | no | How the landing page lists apps: `listed` (default), `name`, `newest` or `app-id`. See [App order](#app-order) |

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

Each app's card shows its version, the date its release was published, and its license. It links to the app's repository, and to its website, bug tracker and donation page when its metainfo lists them (`<url type="homepage">`, `bugtracker` and `donation`, `https:` only); an app without one has no link for it. The page's footer shows when it was last published, in each visitor's own time zone; a Pond only republishes when something changes, so that is when the page last changed, not when it was last checked.

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

## Theme

```yaml
  theme:
    accent: 1c7a4f
    accent-dark: 8ff0a4
    background: f6f5f4
    background-dark: "#1d1d1d"
```

All four are optional hex colors, 3 or 6 digits. Write them without `#`, or with `#` inside quotes: YAML reads an unquoted `#1c7a4f` as a comment, and FrogPak reports that.

- `accent` colors links, buttons and the selected tab; `background` is the page color.
- The `-dark` variants apply when the visitor's system is in dark mode. Left out, they are derived from the light colors.
- Text, card, border and code-block colors are derived from the background.
- Derived colors are adjusted until text is readable. Colors you set are used as given; if one is hard to read, the publish warns and suggests a nearby color that passes.
- Readable means the accent has at least 4.5:1 contrast against the page and cards, where links and text use it, and 3:1 against code blocks, where it only colors the copy button's icon. These are the WCAG levels for text and for icons. The default accents, GNOME's blue, pass both.

## Custom stylesheet

`css` adds a stylesheet after FrogPak's own, so its rules win. Use it for anything the theme cannot do. The page's HTML can change between FrogPak versions, so a custom stylesheet may need updating when you upgrade; the theme colors are the stable way to restyle.

## Logos and favicon

- `logo`, `logo-dark` and `favicon` take a path inside the repository or an `https://` URL. SVG and PNG are accepted; SVG is preferred.
- Without `logo`, FrogPak looks for `logo.svg`, then `logo.png`, at the repository root, and likewise `logo-dark.svg` and `logo-dark.png`. With neither, the FrogPak logo is used.
- Wide logos are fine on the page; they are scaled, never stretched. The favicon is made from the logo unless `favicon` is set, so a wide logo produces a warning suggesting a square `favicon`.
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
