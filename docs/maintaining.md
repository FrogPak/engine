# Maintaining the engine

For maintainers of FrogPak/engine and FrogPak/releaser. Both are released the same way.

## Versions

Releases follow semantic versioning. Ponds and apps call `@v1`, a tag that moves to each `1.x.y` release, so only a breaking change gets a new major tag.

Breaking means a pond or app that worked has to change something: a removed or renamed config key or input, a changed default asset name, a different output layout.

## Releasing

1. Update `__version__` in `frogpak/__init__.py` (or `releaser/__init__.py`) and commit.
2. Tag and move the major tag:

   ```
   git tag v1.2.0
   git tag -f v1
   git push origin v1.2.0
   git push -f origin v1
   ```

3. Create a GitHub release for `v1.2.0` with the changes.

Every pond on `@v1` uses the new code at its next run, so test first: point a test pond's workflow at the branch or commit (`@main` or `@<sha>`) and run it.

## Protecting tags

**Settings > Rules > Rulesets > New tag ruleset**, targeting `v*`:

- Restrict deletions and restrict updates.
- Add repository administrators to the bypass list, so the maintainer can still move `v1`.

## Organization settings

- **Settings > Authentication security:** require two-factor authentication.
- Keep the number of people with write access to these two repositories small; their code runs with every pond's signing key.
