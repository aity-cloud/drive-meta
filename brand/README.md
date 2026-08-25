# Aity Drive brand master

The single source every Factory derives its per-platform Branding assets
from (adaptive icon layers, asset catalogues, ICO/ICNS, splash colours).
Edit here, regenerate there; never hand-edit a derived asset.

- `logo.svg` - the Aity mark, identical to the one the Web Client serves
  from `drive.aity.tech/aity/themes/logo.svg` (source: `aity-tech/drive-theme`).
- Wordmark: the estate's mono wordmark family, `AITY DRIVE` (as `AITY MAIL`
  and `AITY CLOUD` in the Keycloak login theme).
- Product name in every user-facing string: **Aity Drive**.

## Palette

Taken verbatim from `aity-platform` `aity-ds.css` (`--red-*`), brand
primary is red-600, "from the logo":

| Token | Hex |
|---|---|
| red-50 | `#fff1f2` |
| red-100 | `#ffe0e3` |
| red-200 | `#ffc3c8` |
| red-300 | `#f58a93` |
| red-400 | `#e64a57` |
| red-500 | `#ce1626` |
| **red-600 (primary)** | **`#b80818`** |
| red-700 (hover) | `#970614` |
| red-800 (active) | `#780611` |
| red-900 | `#5a0a11` |
| red-950 | `#3d070c` |

Neutrals follow the design system's slate scale; on-brand text is white.

## Staging badge

The staging Environment build uses the same icon with a visible corner
badge ("STG") so both builds are told apart on one device; the badge is
generated, not drawn by hand.
