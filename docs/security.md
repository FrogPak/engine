# Security

## What the engine can see

The Pond's workflow passes its signing key to the engine's code, which runs inside your repository's workflow. Anyone who could change that code could read the key. Two settings decide how much you rely on the FrogPak project:

- **Following `@v1`** (the template's default): you get fixes automatically, and you trust the FrogPak repository's maintainers and their account security. The engine repository requires two-factor sign-in and protects its release tags.
- **Pinning a commit:** nothing changes until you approve it.

To pin, replace `@v1` in `.github/workflows/publish.yml` with the full commit SHA of an engine release, followed by its version as a comment so Dependabot can tell which release it is:

```yaml
    uses: FrogPak/engine/.github/workflows/pond.yml@<full commit SHA> # v1.2.0
```

Then let Dependabot propose updates by adding `.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
```

Each update arrives as a pull request you can read before merging.

## Permissions the workflow asks for

| Permission | Used for |
| --- | --- |
| `contents: write` | The empty commit that keeps the hourly schedule active after 50 quiet days |
| `actions: write` | Re-enabling the scheduled workflow |
| `pages: write` | Deploying the site |
| `id-token: write` | Deploying to Pages, and finding the engine's own code at the version you called |

## The signing key

- It has no passphrase; GitHub's secret store protects it.
- Keep the exported `.asc` file offline or in a password manager. Never commit it.
- Anyone with the key can sign content your users' Flatpak installations will trust. If it leaks, create a new key, replace the secret, and tell your users to remove and re-add the remote.

## What visitors' machines trust

Adding a Pond's remote trusts its key for the apps it serves. Flatpak's sandbox still applies to every app, with the permissions each app's manifest declares.

## Content from elsewhere

- Logos fetched from URLs, and app icons from bundles, are published as PNG images, so third-party SVG content is never served from your Pond's address.
- Addresses from a forge's API are used only if they are `http` or `https`, and text such as repository descriptions is kept to one line in the `.flatpakref` files.
- Zips are read without using the names inside them as paths, so a zip cannot write files outside its working folder, and extraction stops at fixed size limits.
- Bundles are imported into a separate staging repository first and checked against the app ID and architecture in `frogpak.yml`, so a mislabeled bundle cannot replace another app.
