"""The 西安天然气 integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    SCAN_INTERVAL,
    CONF_USER_ID,
    CONF_CARD_ID,
    CONF_XIUZHENG,
    CONF_TOKEN_S,
    DEFAULT_USER_ID,
    DEFAULT_CARD_ID,
    DEFAULT_XIUZHENG,
    DEFAULT_TOKEN_S,
)
from .http_client import XianGasClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the 西安天然气 component."""
    hass.data.setdefault(DOMAIN, {})
    
    # If no config entry exists, create one with default values
    if not hass.config_entries.async_entries(DOMAIN):
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_IMPORT},
                data={
                    CONF_USER_ID: DEFAULT_USER_ID,
                    CONF_CARD_ID: DEFAULT_CARD_ID,
                    CONF_XIUZHENG: DEFAULT_XIUZHENG,
                    CONF_TOKEN_S: DEFAULT_TOKEN_S,
                },
            )
        )
    
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up 西安天然气 from a config entry."""
    # 优先从选项中获取配置，如果没有则从数据中获取
    user_id = entry.options.get(CONF_USER_ID, entry.data.get(CONF_USER_ID, DEFAULT_USER_ID))
    card_id = entry.options.get(CONF_CARD_ID, entry.data.get(CONF_CARD_ID, DEFAULT_CARD_ID))
    xiuzheng = entry.options.get(CONF_XIUZHENG, entry.data.get(CONF_XIUZHENG, DEFAULT_XIUZHENG))
    token_s = entry.options.get(CONF_TOKEN_S, entry.data.get(CONF_TOKEN_S, DEFAULT_TOKEN_S))
    
    _LOGGER.info("设置修正值: %s", xiuzheng)
    
    client = XianGasClient(
        user_id,
        card_id,
        xiuzheng,
        token_s,
    )

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=client.async_get_data,
        update_interval=SCAN_INTERVAL,
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator and client for platforms to access
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up all platforms for this device/entry
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Add update listener for config entry changes
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Clean up
    if unload_ok:
        coordinator = hass.data[DOMAIN][entry.entry_id]
        client = coordinator.update_method.__self__
        await client.async_close()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when it changed."""
    _LOGGER.info("重新加载配置项，修正值: %s", entry.options.get(CONF_XIUZHENG))
    await hass.config_entries.async_reload(entry.entry_id)
