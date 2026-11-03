# Feeding a pond

A pond needs one thing from an app: a release whose files it can match, one `.flatpak` bundle per architecture. How the bundles are built is up to the app's developer. There are three ways to provide them.

## 1. FrogPak releaser

[FrogPak/releaser](https://github.com/FrogPak/releaser) is a workflow you add to the app repository. It builds the bundles for x86_64 and aarch64, checks that versions agree, publishes the release when the version in your metainfo changes, and triggers your ponds. Its README has the details.

Its bundles use the default names, so the pond entry needs only `repo`.

## 2. Your own workflow, with a trigger

Keep your build and add one step after a release is published, so ponds update at once:

```yaml
- name: Trigger ponds
  if: ${{ !contains(github.ref_name, '-') }}
  env:
    GH_TOKEN: ${{ secrets.POND_TOKEN }}
  run: gh workflow run publish.yml --repo OWNER/POND
```

The `if` skips pre-releases, which ponds ignore. Set `assets` in the pond's entry if your file names differ from `{app_id}-{arch}.flatpak`.

## 3. Your own workflow, no trigger

Nothing to add. The pond finds the release at its next hourly check.

Apps released on Codeberg, Forgejo or Gitea use option 3, or option 2 by running the same `gh` command from their own CI. GitLab support is planned.

## Triggering a pond

A trigger starts the pond's normal check early; a trigger with nothing new costs one quick check.

`POND_TOKEN` is a fine-grained personal access token, created by someone with write access to the pond:

1. GitHub **Settings > Developer settings > Personal access tokens > Fine-grained tokens > Generate new token**.
2. **Resource owner:** the pond's owner. **Repository access:** only the pond repository.
3. **Permissions > Actions:** Read and write. Nothing else.
4. Add the token to the app repository as an Actions secret named `POND_TOKEN`.

The token can only start the pond's workflows. A pond owned by an organization may require the organization to allow fine-grained tokens first.

## Release files

- Pre-releases are never published to a pond.
- Each bundle must contain the app ID and architecture its pond entry expects; others are skipped.
- Bundles should be built with `flatpak build-bundle --runtime-repo=https://dl.flathub.org/repo/flathub.flatpakrepo`, so installing an app also finds its runtime.
- Metainfo in the app gives the pond its name, summary and version, and software centers their screenshots and release notes. Without it, the pond uses the repository description and the release tag.
