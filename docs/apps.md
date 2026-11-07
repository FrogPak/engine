# Feeding a Pond

A Pond needs one thing from an app: a release whose files it can match, one `.flatpak` bundle per architecture. How the bundles are built is up to the app's developer. There are three ways to provide them.

## 1. FrogPak releaser

[FrogPak/releaser](https://github.com/FrogPak/releaser) is a workflow you add to the app repository. It builds the bundles for x86_64 and aarch64, checks that versions agree, publishes the release when the version in your metainfo changes, and triggers your Ponds. Its README has the details.

Its bundles use the default names, so the Pond entry needs only `repo`.

## 2. Your own workflow, with a trigger

Keep your build and add one step after a release is published, so Ponds update at once:

```yaml
- name: Trigger Ponds
  if: ${{ !contains(github.ref_name, '-') }}
  env:
    GH_TOKEN: ${{ secrets.POND_TOKEN }}
  run: gh workflow run publish.yml --repo OWNER/POND
```

The `if` skips pre-releases, which Ponds ignore. Set `assets` in the Pond's entry if your file names differ from `{app_id}-{arch}.flatpak`.

## 3. Your own workflow, no trigger

Nothing to add. The Pond finds the release at its next hourly check.

Apps released on Codeberg, Forgejo or Gitea use option 3, or option 2 by running the same `gh` command from their own CI. GitLab support is planned.

## Triggering a Pond

A trigger starts the Pond's normal check early; a trigger with nothing new costs one quick check.

`POND_TOKEN` is a fine-grained personal access token, created by someone with write access to the Pond:

1. GitHub **Settings > Developer settings > Personal access tokens > Fine-grained tokens > Generate new token**.
2. **Resource owner:** the Pond's owner. **Repository access:** only the Pond repository.
3. **Permissions > Actions:** Read and write. Nothing else.
4. Add the token to the app repository as an Actions secret named `POND_TOKEN`.

The token can only start the Pond's workflows. A Pond owned by an organization may require the organization to allow fine-grained tokens first.

## Release files

- Pre-releases are never published to a Pond.
- Each bundle must contain the app ID and architecture its Pond entry expects; others are skipped.
- Bundles should be built with `flatpak build-bundle --runtime-repo=https://dl.flathub.org/repo/flathub.flatpakrepo`, so installing an app also finds its runtime.
- Metainfo in the app gives the Pond its name, summary and version, and software centers their screenshots and release notes. Without it, the Pond uses the repository description and the release tag.

## Badges

Every Pond publishes badges that help people find its apps, with a page to copy them from at the Pond's address followed by `badges/`, such as `https://frogpak.org/demo/badges/`. The landing page does not link to it; each publish run's summary does.

- **Button:** "Get it on" and the Pond's name, with its icon, in a light and a dark version. The page has it as HTML, which switches between the two with GitHub's appearance, and as Markdown with the light version.
- **Version badges:** the Pond's name and the version of the app it publishes, in the Pond's accent color, one per app. The page has each as Markdown, linking to the app's card.

Badges are rebuilt with every publish, so a version badge always shows the version the Pond serves. Their addresses never change, so they can also be written by hand:

| File | Address |
| --- | --- |
| Button, light | `<Pond address>badges/button-light.svg` |
| Button, dark | `<Pond address>badges/button-dark.svg` |
| Version badge | `<Pond address>badges/<app ID>.svg` |
| An app's card, to link to | `<Pond address>#<app ID>` |

`apps.json` lists the same addresses, under `badges` and each app's `badge`.
