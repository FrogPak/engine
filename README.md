# FrogPak

**Flatpak Remotes On GitHub Pages Automation Kit:** publish your apps as a signed Flatpak remote, served by GitHub Pages. No server needed.

A FrogPak deployment is called a **Pond**: one GitHub repository that collects your apps' release bundles, builds a signed Flatpak repository from them, and publishes it with a landing page. People add your remote once and install and update your apps like any other Flatpak.

- Signed with your own key; Flatpak verifies every download.
- Apps come from their GitHub releases, built however you like. The optional [FrogPak releaser](https://github.com/FrogPak/releaser) builds and releases them for you.
- Checks for new releases hourly and rebuilds only when something changed; apps can trigger an update the moment they release.
- A landing page with install commands, your logo and colors, in light and dark mode, and each app's version, release date and license.
- Badges for app READMEs: a "Get it on" button for the Pond and a version badge for each app.

![A Pond's landing page, split diagonally between light and dark mode: system, light and dark buttons beside the Source link, the command to add the remote, with System and User tabs, All, x86_64 and aarch64 buttons beside the Apps heading, and one card per app with its icon, version, summary, release date, license, links and an Install button, one with its menu open to show the .flatpakref download and install command](docs/images/landing-page.png)

## Start a Pond

Use the [Pond template](https://github.com/FrogPak/pond-template), then follow [Setting up a Pond](docs/setup.md).

## Documentation

- [Setting up a Pond](docs/setup.md)
- [Configuration reference](docs/configuration.md)
- [Feeding a Pond](docs/apps.md)
- [Security](docs/security.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Maintaining the engine](docs/maintaining.md)

## This repository

- `.github/workflows/publish-pond.yml`: the reusable workflow Ponds call.
- `frogpak/`: the engine (`python3 -m frogpak check | poll | publish`). `frogpak/sources/` has one module per forge, and nothing outside it may assume a forge.
- `tests/`: unit tests and `local_publish.py`, which runs a full publish offline from a folder of bundles. [Maintaining the engine](docs/maintaining.md#running-it-locally) has the commands and what they need.

## The frog

FrogPak's mascot is the golden mantella (*Mantella aurantiaca*), a tiny orange frog found only in a few small areas of forest and wetland in eastern Madagascar. It is listed as Endangered: its habitat is being lost to logging, mining and farming, and collection for the pet trade adds to the pressure. [Chester Zoo](https://www.chesterzoo.org/our-zoo/animals/golden-mantella-frog/) and its partner [Madagasikara Voakajy](https://www.madagasikara-voakajy.org/) work to protect it in the wild. Please consider a [donation](https://conservationallies.org/partners/madagasikara-voakajy/) if it is within your means.

## License

GPL-3.0-or-later. Ponds created from the template, and the apps they publish, are not covered by it.
