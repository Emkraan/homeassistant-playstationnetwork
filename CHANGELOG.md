# Changelog

## 2026.5.3-beta (2026-05-11)

### Changed
- Repository renamed from `ha-playstation-network` to `homeassistant-playstation-network` to follow standard naming convention
- Updated all internal URL references accordingly

## 2026.5.2-beta (2026-05-11)

### Fixed
- Removed all `[%key:...]` references from `strings.json` and `translations/en.json` — this syntax is only valid in HA core and caused `MALFORMED_ARGUMENT` errors in custom components. All strings are now fully resolved literals
- Fixed `documentation` URL in `manifest.json` pointing to HA docs instead of this repo (controls the help `?` button in the config flow)

## 2026.5.1-beta (2026-05-11)

### Fixed
- `MALFORMED_ARGUMENT` translation error caused by percent-encoded characters in the bookmarklet URL inside `data_description` — the bookmarklet has been moved to the `description` field and `data_description` is now plain text

## 2026.5.0-beta (2026-05-11)

### Added
- Initial release as a HACS-installable custom component replacing the built-in `playstation_network` integration
- **Token persistence**: After the first authentication, the full token response (access token + refresh token + expiry timestamps) is stored in the config entry. On every HA restart the integration injects the stored token back into the library, skipping NPSSO re-authentication for up to 60 days
- **Silent token refresh**: After each successful 30-second coordinator refresh cycle, any new token issued by Sony is automatically persisted — the 60-day clock resets on every HA restart that occurs within the window
- **Improved setup UX**: Config flow description includes a direct link to the Sony SSO cookie endpoint and an optional bookmarklet that extracts the NPSSO cookie automatically when clicked on any PlayStation Network page
- All entities, unique IDs, and state values are identical to the built-in integration — existing automations and dashboards require no changes
- Diagnostics output redacts sensitive token fields (`access_token`, `refresh_token`, `id_token`, `token_response`)
