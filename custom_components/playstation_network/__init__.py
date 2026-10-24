"""The PlayStation Network integration."""

from functools import partial

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_NPSSO, CONF_TOKEN_RESPONSE
from .coordinator import (
    PlaystationNetworkConfigEntry,
    PlaystationNetworkFriendDataCoordinator,
    PlaystationNetworkFriendlistCoordinator,
    PlaystationNetworkGroupsUpdateCoordinator,
    PlaystationNetworkRuntimeData,
    PlaystationNetworkTrophyTitlesCoordinator,
    PlaystationNetworkUserDataCoordinator,
    persist_current_token,
)
from .helpers import PlaystationNetwork

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.IMAGE,
    Platform.MEDIA_PLAYER,
    Platform.NOTIFY,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: PlaystationNetworkConfigEntry) -> bool:
    """Set up Playstation Network from a config entry."""

    # Pass any previously persisted token_response so the library can skip
    # re-authentication as long as the refresh token has not expired.
    psn = PlaystationNetwork(
        hass,
        entry.data[CONF_NPSSO],
        token_response=entry.data.get(CONF_TOKEN_RESPONSE),
    )

    # Sony rotates the refresh token on every renewal, on whichever worker
    # thread triggers it. Store each rotated pair on the entry the moment it
    # rotates, so a restart can never find a spent token. The rotation report
    # arrives on that worker thread, so hop to the event loop for the entry
    # update; a token change alone never needs a reload.
    psn.on_token_rotated = partial(
        hass.loop.call_soon_threadsafe,
        persist_current_token,
        hass,
        entry,
        psn,
    )

    coordinator = PlaystationNetworkUserDataCoordinator(hass, psn, entry)
    await coordinator.async_config_entry_first_refresh()

    trophy_titles = PlaystationNetworkTrophyTitlesCoordinator(hass, psn, entry)

    groups = PlaystationNetworkGroupsUpdateCoordinator(hass, psn, entry)
    await groups.async_config_entry_first_refresh()

    friends_list = PlaystationNetworkFriendlistCoordinator(hass, psn, entry)

    friends = {}

    for subentry_id, subentry in entry.subentries.items():
        friend_coordinator = PlaystationNetworkFriendDataCoordinator(hass, psn, entry, subentry)
        await friend_coordinator.async_config_entry_first_refresh()
        friends[subentry_id] = friend_coordinator

    entry.runtime_data = PlaystationNetworkRuntimeData(
        coordinator, trophy_titles, groups, friends, friends_list
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: PlaystationNetworkConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
