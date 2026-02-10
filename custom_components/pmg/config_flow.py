"""Config flow for Proxmox Mail Gateway."""

from __future__ import annotations

import logging
import asyncio
import voluptuous as vol
from yarl import URL

from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from aiohttp import ClientError

from .api import PMGApiClient, PMGApiError
from .const import (
    CONF_REALM,
    CONF_SCAN_INTERVAL,
    CONF_STATS_DAYS,
    CONF_VERIFY_SSL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_STATS_DAYS,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)


async def _test_connection(hass: HomeAssistant, data: dict) -> None:
    session = async_get_clientsession(hass)
    client = PMGApiClient(
        session=session,
        host=data[CONF_HOST],
        port=data[CONF_PORT],
        username=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
        realm=data[CONF_REALM],
        verify_ssl=data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
    )
    try:
        await client.async_login()
        await client.async_get("/version")
    except (ClientError, asyncio.TimeoutError, PMGApiError) as err:
        raise PMGApiError(str(err)) from err


class PMGConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Proxmox Mail Gateway."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            if "://" in user_input[CONF_HOST]:
                url = URL(user_input[CONF_HOST])
                if url.host:
                    user_input[CONF_HOST] = url.host
                if url.port:
                    user_input[CONF_PORT] = url.port

            try:
                await _test_connection(self.hass, user_input)
            except PMGApiError as err:
                logging.getLogger(__name__).exception(
                    "PMG config flow connection failed: %s", err
                )
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(
                    f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_HOST],
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_REALM: user_input[CONF_REALM],
                        CONF_VERIFY_SSL: user_input.get(
                            CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL
                        ),
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int),
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_REALM, default="pmg"): str,
                vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return PMGOptionsFlow(config_entry)


class PMGOptionsFlow(config_entries.OptionsFlow):
    """Options flow for PMG."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.entry = entry

    async def async_step_init(self, user_input: dict | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_VERIFY_SSL,
                    default=self.entry.options.get(
                        CONF_VERIFY_SSL,
                        self.entry.data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
                    ),
                ): bool,
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=self.entry.options.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=10, max=86400)),
                vol.Optional(
                    CONF_STATS_DAYS,
                    default=self.entry.options.get(CONF_STATS_DAYS, DEFAULT_STATS_DAYS),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=365)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
