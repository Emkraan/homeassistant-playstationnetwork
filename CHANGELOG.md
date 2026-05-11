# Changelog

## 2026.5.0-beta (2026-05-11)

### Added
- Initial release as a HACS-installable custom component replacing the built-in `playstation_network` integration
- **Token persistence**: After the first authentication, the full token response (access token + refresh token + expiry timestamps) is stored in the config entry. On every HA restart the integration injects the stored token back into the library, skipping NPSSO re-authentication for up to 60 days
- **Silent token refresh**: After each successful 30-second coordinator refresh cycle, any new token issued by Sony is automatically persisted — the 60-day clock resets on every HA restart that occurs within the window
- **Improved setup UX**: Config flow description includes a direct link to the Sony SSO cookie endpoint and an optional bookmarklet that extracts the NPSSO cookie automatically when clicked on any PlayStation Network page
- All entities, unique IDs, and state values are identical to the built-in integration — existing automations and dashboards require no changes
- Diagnostics output redacts sensitive token fields (`access_token`, `refresh_token`, `id_token`, `token_response`)
