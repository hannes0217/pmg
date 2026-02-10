"""Diagnostics support for Proxmox Mail Gateway."""

from __future__ import annotations

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from homeassistant.const import CONF_HOST, CONF_PORT, CONF_USERNAME

from .const import CONF_REALM, CONF_VERIFY_SSL, DOMAIN

TO_REDACT = {"password", "ticket"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    coordinator = hass.data[DOMAIN][entry.entry_id]

    data = {
        "config": {
            CONF_HOST: entry.data.get(CONF_HOST),
            CONF_PORT: entry.data.get(CONF_PORT),
            CONF_USERNAME: entry.data.get(CONF_USERNAME),
            CONF_REALM: entry.data.get(CONF_REALM),
            CONF_VERIFY_SSL: entry.options.get(CONF_VERIFY_SSL),
        },
        "data": coordinator.data,
    }

    return async_redact_data(data, TO_REDACT)
