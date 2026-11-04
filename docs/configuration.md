# Configuration reference

A Pond is configured by `frogpak.yml` at the root of its repository. Unknown or misspelt keys are errors, and every problem in the file is reported at once.

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

YAML guesses types for unquoted text: `no` becomes false and `1.10` becomes the number 1.1. FrogPak reports these instead of guessing along; put such values in quotes.

## apps

Each key is an app ID, such as `org.example.Notes`. Under it:

| Key | Required | Meaning |
| --- | --- | --- |
| `repo` | yes | Where the releases are: `owner/repo` on GitHub, or a full `https://` address on GitHub, Codeberg, Forgejo or Gitea |
| `assets` | no | Pattern for the release files; default `{app_id}-{arch}.flatpak` |
| `forge` | no | `github`, `forgejo`, `gitea` or `gitlab`, for a self-hosted forge FrogPak cannot recognize |

The Pond publishes each app's newest release that is not a pre-release. Apps that cannot be published, such as one with no release or no matching files, are skipped with a warning and the rest are published.

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

## Custom stylesheet

`css` adds a stylesheet after FrogPak's own, so its rules win. Use it for anything the theme cannot do. The page's HTML can change between FrogPak versions, so a custom stylesheet may need updating when you upgrade; the theme colors are the stable way to restyle.

## Logos and favicon

- `logo`, `logo-dark` and `favicon` take a path inside the repository or an `https://` URL. SVG and PNG are accepted; SVG is preferred.
- Without `logo`, FrogPak looks for `logo.svg`, then `logo.png`, at the repository root, and likewise `logo-dark.svg` and `logo-dark.png`. With neither, the FrogPak logo is used.
- Wide logos are fine on the page; they are scaled, never stretched. The favicon is made from the logo unless `favicon` is set, so a wide logo produces a warning suggesting a square `favicon`.
- URLs are fetched at every publish. If one cannot be fetched, the publish continues with the default and a warning. SVGs from URLs are published as PNG images.
