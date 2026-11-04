# Maintaining the engine

For maintainers of FrogPak/engine and FrogPak/releaser. Both are released the same way.

## Versions

Releases follow semantic versioning. Ponds and apps call `@v1`, a tag that moves to each `1.x.y` release, so only a breaking change gets a new major tag.

Breaking means a Pond or app that worked has to change something: a removed or renamed config key or input, a changed default asset name, a different output layout.

## Releasing

1. Add the version's entry at the top of `CHANGELOG.md`, set `__version__` in `frogpak/__init__.py` (or `releaser/__init__.py`) to the same number, and commit. The tests fail when the two differ, and on a release tag that does not match them.
2. Tag and move the major tag:

   ```
   git tag v1.2.0
   git tag -f v1
   git push origin v1.2.0
   git push -f origin v1
   ```

3. Create a GitHub release for `v1.2.0` with the changes.

Every Pond on `@v1` uses the new code at its next run, so test first: point a test Pond's workflow at the branch or commit (`@main` or `@<sha>`) and run it.

## Protecting tags

**Settings > Rules > Rulesets > New tag ruleset**, targeting `v*`:

- Restrict deletions and restrict updates.
- Add repository administrators to the bypass list, so the maintainer can still move `v1`.

## Documentation site

[frogpak.github.io](https://frogpak.github.io/) is built by [FrogPak/frogpak.github.io](https://github.com/FrogPak/frogpak.github.io) from this repository's `README.md` and `docs/`. The **Docs** workflow here starts that build after a push to `main` that changes them. It needs a `SITE_TOKEN` secret in this repository: a fine-grained token with resource owner **FrogPak**, access to only `FrogPak/frogpak.github.io`, and **Actions: Read and write**. Without it, the site still rebuilds daily.

A link to a missing page or heading fails the site build, so check the **Build site** run after changing links.

## Organization settings

- **Settings > Authentication security:** require two-factor authentication.
- Keep the number of people with write access to these two repositories small; their code runs with every Pond's signing key.
