<div align="center">

<img src="https://raw.githubusercontent.com/Emkraan/homeassistant-playstationnetwork/main/.github/homeassistant-playstationnetwork.png" alt="PlayStation Network" width="256"/>

# PlayStation Network for Home Assistant

Track your PlayStation Network presence, trophies, and active gaming sessions — with seamless token refresh that eliminates constant reauthentication.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/v/release/Emkraan/homeassistant-playstationnetwork)](https://github.com/Emkraan/homeassistant-playstationnetwork/releases)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1.0%2B-blue)](https://www.home-assistant.io/)
[![License](https://img.shields.io/github/license/Emkraan/homeassistant-playstationnetwork)](LICENSE)

</div>

---

<div align="center">

⚠️ 🚨 **This is an unofficial integration and is not affiliated with or endorsed by Sony Interactive Entertainment.** 🚨 ⚠️

</div>

---

## Table of Contents

- [Why This Exists](#why-this-exists)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Entities](#entities)
- [Automations](#automations)
- [Troubleshooting](#troubleshooting)
- [How It Works](#how-it-works)
- [License](#license)

---

## Why This Exists

The built-in `playstation_network` integration requires manual reauthentication whenever its stored NPSSO token is invalidated — typically when you log out of PlayStation in the same browser session you used to get the token, or if HA is offline for an extended period.

This integration fixes that by **persisting the refresh token** after the first setup. As long as HA restarts at least once every 60 days, authentication is renewed automatically and you will never see a reauth prompt.

---

## Features

- **Persistent authentication** — stores the OAuth refresh token after first setup; silent renewal on every restart
- **Improved setup flow** — direct link to the Sony SSO cookie page and an optional browser bookmarklet for one-click token extraction
- **Drop-in replacement** — same domain (`playstation_network`), identical entity IDs and state values; existing automations and dashboards keep working after switching
- Online status sensor (Online, Away, Offline, Online on PS App)
- Active game / media player per console (PS5, PS4, PS3, PS Vita, PC)
- Game artwork image entity
- PS Plus subscription status
- Trophy level and progress sensors
- Bronze / Silver / Gold / Platinum trophy count sensors
- Avatar image entity
- Direct message and group message notify entities
- Friend tracking via subentries (add friends to monitor their online status)

---

## Requirements

| Requirement | Details |
|---|---|
| Home Assistant | 2024.1.0 or later |
| HACS | Any version supporting custom repositories |
| PlayStation Network account | Free or PS Plus |
| NPSSO token | One-time setup — see [Configuration](#configuration) |

---

## Installation

### Via HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Emkraan&repository=homeassistant-playstationnetwork&category=integration)

1. Click the badge above, or open HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/Emkraan/homeassistant-playstationnetwork` as an **Integration**
3. Search for **PlayStation Network** and install
4. Restart Home Assistant

### Replacing the built-in integration

If you currently use the built-in PlayStation Network integration:

1. Go to **Settings → Devices & Services → PlayStation Network** and delete the existing entry
2. Install this integration via HACS and restart HA
3. Add the integration — your entity IDs will be preserved

---

## Configuration

### Getting your NPSSO token

The NPSSO token is a session cookie that Sony issues when you log in to the PlayStation website. You only need to provide it once.

**Option A — Manual (always works):**
1. Log in to your [PlayStation account](https://www.playstation.com)
2. [Open this link](https://ca.account.sony.com/api/v1/ssocookie) — a JSON page like `{"npsso":"<64-char token>"}` will appear
3. Copy the value of `npsso` and paste it into the HA setup form

**Option B — Bookmarklet (one-time install, then one click):**

Drag the link below to your browser bookmarks bar. When clicked on any PlayStation Network page while logged in, it will show your NPSSO token in a prompt for easy copying.

> **[Get NPSSO Token](javascript:(function(){var%20n=document.cookie.split(';').map(c=>c.trim()).find(c=>c.startsWith('npsso='));if(n){var%20token=n.split('=')[1];prompt('Copy%20your%20NPSSO%20token:',token);}else{alert('NPSSO%20cookie%20not%20found.%20Make%20sure%20you%20are%20logged%20in%20to%20PlayStation%20Network.');}})()**

**Important:** Do not log out of your PlayStation account in the same browser session after obtaining the token. Logging out immediately invalidates the NPSSO cookie.

### After setup

Once configured, the integration handles all token renewal automatically. Reauth should never be required unless:
- HA is offline for more than 60 consecutive days
- You revoke the session from your PSN account security settings
- Sony invalidates the session server-side (password change, suspicious activity)

---

## Entities

### Your account

| Platform | Entity | Description |
|---|---|---|
| `sensor` | Online status | `online` / `away` / `offline` / `online on ps app` |
| `sensor` | Now playing | Title of the game currently being played |
| `sensor` | Online ID | Your PSN username |
| `sensor` | Last online | Timestamp of last online activity |
| `sensor` | Trophy level | Current trophy level (1–999) |
| `sensor` | Next level | Progress toward next trophy level (%) |
| `sensor` | Platinum trophies | Total platinum trophies earned |
| `sensor` | Gold trophies | Total gold trophies earned |
| `sensor` | Silver trophies | Total silver trophies earned |
| `sensor` | Bronze trophies | Total bronze trophies earned |
| `binary_sensor` | Subscribed to PlayStation Plus | On when PS Plus subscription is active |
| `image` | Avatar | Your PSN avatar (XL size) |
| `image` | Now playing image | Cover art of the game currently being played |
| `image` | Share profile | Your shareable PSN profile QR/link image |
| `media_player` | PlayStation 5 | Active session on PS5 |
| `media_player` | PlayStation 4 | Active session on PS4 |
| `media_player` | PlayStation 3 | Active session on PS3 |
| `media_player` | PS Vita | Active session on PS Vita |
| `media_player` | PlayStation PC | Active session on PS PC |
| `notify` | Direct message / Group | Send PSN messages to friends or groups |

### Friend tracking (subentries)

After setup, click **Add friend** on the integration card to track a friend's online status. Each friend gets the same sensor and image entities scoped to their account.

---

## Automations

### Notify when a friend comes online

```yaml
automation:
  trigger:
    - platform: state
      entity_id: sensor.friend_online_status
      to: "availabletoplay"
  action:
    - service: notify.mobile_app_my_phone
      data:
        message: "{{ trigger.to_state.attributes.friendly_name }} just came online on PSN!"
```

### Turn on TV when PS5 session starts

```yaml
automation:
  trigger:
    - platform: state
      entity_id: media_player.playstation_5
      to: "playing"
  action:
    - service: media_player.turn_on
      target:
        entity_id: media_player.living_room_tv
```

### Daily trophy progress notification

```yaml
automation:
  trigger:
    - platform: time
      at: "20:00:00"
  condition:
    - condition: state
      entity_id: sensor.online_status
      state: "availabletoplay"
  action:
    - service: notify.mobile_app_my_phone
      data:
        message: >
          PSN Trophy Level: {{ states('sensor.trophy_level') }}
          ({{ states('sensor.next_level') }}% to next level)
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Reauth prompt immediately after setup | NPSSO obtained in the same browser session then logged out | Get a fresh NPSSO without logging out afterward |
| Reauth prompt after 60+ days of HA downtime | Refresh token expired | Re-enter NPSSO via the reauth flow |
| Entities unavailable / update errors | PSN API outage or rate limit | Wait a few minutes; integration will recover automatically |
| Friend status not updating | Friend has set their PSN profile to private | Privacy settings block presence data — this cannot be worked around |
| `PSNAWPNotFoundError` on friend subentry | Friend deleted their account or changed online ID | Remove and re-add the subentry |

### Enable debug logging

Add to `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.playstation_network: debug
```

Then check **Settings → System → Logs** and filter for `playstation_network`.

---

## How It Works

### Authentication

PSN uses an unofficial OAuth2-style flow built on Sony's internal mobile app credentials (reverse-engineered from the PlayStation Android app). The flow is:

1. **NPSSO → authorization code** — a GET to Sony's authorize endpoint with the NPSSO cookie returns a one-time auth code
2. **Auth code → token pair** — a POST to the token endpoint returns an access token (~1 hour TTL) and a refresh token (~60 days TTL)
3. **Silent refresh** — before each API call, the library checks if the access token is expired and exchanges the refresh token for a new pair automatically

This integration extends that behavior by **persisting the token pair to the HA config entry** after each refresh. On restart, the stored token is injected back into the library, bypassing steps 1 and 2 entirely for up to 60 days.

### Data polling

| Coordinator | Interval | Data |
|---|---|---|
| User data | 30 seconds | Presence, active sessions, trophy summary, profile |
| Trophy titles | 1 day | Full trophy title list (used for PS Vita game art lookup) |
| Groups | 3 hours | PSN group chat list for notify entities |
| Friends list | 3 hours | Friend list for subentry auto-discovery |
| Friend status | ~180s (scales with friend count) | Per-friend presence and trophy summary |

---

## License

MIT — see [LICENSE](LICENSE)
