"""Proxmox Mail Gateway integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import PMGApiClient, PMGApiError
from .const import (
    CONF_REALM,
    CONF_SCAN_INTERVAL,
    CONF_STATS_DAYS,
    CONF_VERIFY_SSL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_STATS_DAYS,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    registry = er.async_get(hass)
    for reg_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
        if (
            reg_entry.domain == "sensor"
            and reg_entry.platform == DOMAIN
            and "_v2_" not in reg_entry.unique_id
        ):
            registry.async_remove(reg_entry.entity_id)

    session = async_get_clientsession(hass)
    client = PMGApiClient(
        session=session,
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        realm=entry.data[CONF_REALM],
        verify_ssl=entry.options.get(
            CONF_VERIFY_SSL,
            entry.data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
        ),
    )

    coordinator = PMGDataUpdateCoordinator(hass, client, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


class PMGDataUpdateCoordinator(DataUpdateCoordinator[dict]):
    """Coordinator for PMG data."""

    def __init__(self, hass: HomeAssistant, client: PMGApiClient, entry: ConfigEntry) -> None:
        self.client = client
        self.entry = entry
        update_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            logger=logging.getLogger(__name__),
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> dict:
        try:
            version = await self.client.async_get("/version")

            nodes_data = await self.client.async_get("/nodes") or []
            nodes = {}
            updates: dict[str, Any] = {}
            for node in nodes_data:
                node_name = node.get("node") or node.get("name")
                if not node_name:
                    continue
                status = await self.client.async_get(f"/nodes/{node_name}/status")
                nodes[node_name] = status or {}
                try:
                    updates_data = await self.client.async_get(
                        f"/nodes/{node_name}/apt/update"
                    )
                except PMGApiError as err:
                    if (
                        "404" in str(err)
                        or "401" in str(err)
                        or "403" in str(err)
                        or "501" in str(err)
                        or "not implemented" in str(err).lower()
                    ):
                        updates_data = None
                    else:
                        raise
                updates[node_name] = updates_data

            stats_days = self.entry.options.get(CONF_STATS_DAYS, DEFAULT_STATS_DAYS)
            now = dt_util.utcnow()
            end = now.replace(hour=23, minute=59, second=59, microsecond=0)
            start = (end - timedelta(days=stats_days - 1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            mail_stats = await self.client.async_get(
                "/statistics/mail",
                params={"starttime": int(start.timestamp()), "endtime": int(end.timestamp())},
            )

            quarantine_params = {
                "starttime": int(start.timestamp()),
                "endtime": int(end.timestamp()),
            }
            spam_status = await self.client.async_get("/quarantine/spamstatus")
            virus_status = await self.client.async_get("/quarantine/virusstatus")

            return {
                "version": version,
                "nodes": nodes,
                "updates": updates,
                "mail_stats": mail_stats,
                "spam_status": spam_status,
                "virus_status": virus_status,
            }
        except PMGApiError as err:
            raise UpdateFailed(str(err)) from err
