# Setting up a Pond

A Pond is your own Flatpak remote: a GitHub repository that FrogPak turns into a signed Flatpak repository with a landing page, served by GitHub Pages. Setup takes about fifteen minutes and two terminal commands on a Linux machine.

## Create the repository

1. Open [FrogPak/pond-template](https://github.com/FrogPak/pond-template) and choose **Use this template > Create a new repository**.
2. Pick a name. It becomes part of the address: a repository `mypond` owned by `alex` is served at `https://alex.github.io/mypond/`.
3. Make it **public**. GitHub Pages is free only for public repositories, and so is the arm64 build runner apps use.

## GitHub Pages

In the new repository, open **Settings > Pages** and set **Source** to **GitHub Actions**.

A custom domain set on the same page works too; FrogPak reads the address from GitHub.

## Signing key

Flatpak checks that everything it downloads was signed by the key it trusts for your remote. The key is created once, on your own machine, and kept as a repository secret.

1. On any Linux machine with `gpg`, run these two commands. Pick a name that is unique among your keys.

   ```
   gpg --batch --passphrase '' --quick-generate-key "My Pond signing key" rsa4096 sign never
   gpg --armor --export-secret-keys "My Pond signing key" > pond-signing-key.asc
   ```

2. Open **Settings > Secrets and variables > Actions > New repository secret**. Name it `GPG_PRIVATE_KEY` and paste the whole content of `pond-signing-key.asc`, including the `BEGIN` and `END` lines.
3. Keep `pond-signing-key.asc` somewhere safe, such as a password manager, and never commit it. The template's `.gitignore` excludes `.asc` and `.gpg` files.

The key has no passphrase because the workflow cannot type one; GitHub's secret store protects it instead.

If the key is ever lost, create a new one and replace the secret. Everyone who added your remote then has to remove it and add it again, because the old key no longer matches.

## Configure the Pond

Edit `frogpak.yml` in the repository. The minimum is a title, a remote name and your apps:

```yaml
pond:
  title: Alex's Apps
  remote: alex

apps:
  org.example.Notes:
    repo: alex/notes
```

`remote` is the name people type, as in `flatpak install alex org.example.Notes`. Each app needs a GitHub release with a `.flatpak` file per architecture; [Feeding a Pond](apps.md) explains the options. The [configuration reference](configuration.md) covers logos, colors and asset names.

## Publish

Open **Actions > Publish > Run workflow**. The first run takes a few minutes. When it finishes, the landing page is at the address from [the first step](#create-the-repository), with the command for adding your remote.

If something is missing, the run stops with a message naming it; [Troubleshooting](troubleshooting.md) lists the common ones.

## What happens next

- Every hour, the Pond checks each app's latest release and rebuilds only when something changed.
- A push to the repository, such as an edit to `frogpak.yml`, rebuilds at once.
- **Run workflow** with **Rebuild even if nothing changed** forces a rebuild.
- Apps can trigger the Pond the moment they release; see [Feeding a Pond](apps.md#triggering-a-pond).
- GitHub stops scheduled workflows in repositories with no activity for 60 days. The Pond keeps itself active, and if the repository has had no commit for 50 days it makes an empty commit to stay that way.
