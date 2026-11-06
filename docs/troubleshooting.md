# Troubleshooting

Messages appear at the top of the workflow run's summary page and in its log.

## The run stops

**"Pond not set up: Settings > Pages > Source must be GitHub Actions"**
Set it as described in [GitHub Pages](setup.md#github-pages). On scheduled runs this is a warning, so an unfinished Pond does not fail every hour.

**"Pond not set up: the GPG_PRIVATE_KEY secret is missing"** or **"No signing key found"**
Add the secret as described in [Signing key](setup.md#signing-key). Check the name is exactly `GPG_PRIVATE_KEY` and that the value includes the `BEGIN` and `END` lines.

**"pond.yml has N problem(s)"**
The log lists each one. The common ones:

- *unknown key*: a misspelt or misplaced key; the message lists the allowed ones.
- *must be text; put it in quotes*: YAML turned a value such as `no` into something else.
- *pond.theme.accent is empty*: an unquoted `#` color; write `1c7a4f` or `"#1c7a4f"`.
- *not a valid Flatpak app ID*: app IDs need at least three parts, such as `org.example.App`.

**"Not deploying: site is N MB of GitHub Pages' 1 GB limit"**
GitHub Pages refuses sites larger than 1 GB, so the publish stops and the live site stays as it was. The message lists the largest apps; remove one, or publish fewer architectures with `arches`. A warning appears from 75% of the limit.

## An app is missing from the page

The log has a warning for every skipped app:

- *has no published release*: the repository has no release or only pre-releases, or `repo` is wrong or private.
- *no asset in v1.0 matches …*: the release has no file matching the app's `assets` pattern. Compare the file names on the release page with the pattern.
- *N assets match … skipped*: the pattern matches several files; make it more specific.
- *contains app/…, expected app/…*: the bundle holds a different app ID or architecture than the Pond entry.

## An app shows the wrong license

The log warns when the sources disagree:

- *the forge reports license A, but the metainfo says B*: the repository's LICENSE file and the app's metainfo name different licenses. The forge's is shown. If the metainfo is right, set `license: meta` for the app, and consider telling its developer.
- *license: A in pond.yml differs from B*: a license in `pond.yml` is only used when neither source states one. Remove it, or ask the app's developer to correct the source that is wrong.
- *license is set to forge (or meta), but … states no license*: that source has nothing; use `auto` to fall back to the other.

## The page didn't update

- Check that the release is not a pre-release.
- Scheduled checks run hourly, and GitHub can delay scheduled runs at busy times. **Actions > Publish > Run workflow** checks at once.
- Browsers and GitHub Pages cache pages for about ten minutes.

## Users see signature errors

An error ending in `public key not found` after a key change means users still trust the old key. They need to remove and re-add the remote:

```
flatpak remote-delete POND_REMOTE
flatpak remote-add POND_REMOTE https://OWNER.github.io/REPOSITORY/index.flatpakrepo
```

## The schedule stopped

GitHub disables scheduled workflows in repositories with 60 days of no activity. The Pond guards against this, but if it happens, open **Actions > Publish** and choose **Enable workflow**.
