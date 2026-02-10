"""API client for Proxmox Mail Gateway."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import aiohttp
from aiohttp import ClientError, ContentTypeError

import asyncio

from .const import COOKIE_NAME


class PMGApiError(Exception):
    """Base error for PMG API."""


@dataclass
class PMGAuth:
    ticket: str
    csrf: str | None


class PMGApiClient:
    """Minimal PMG API client using /api2/json endpoints."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        username: str,
        password: str,
        realm: str,
        verify_ssl: bool,
    ) -> None:
        self._session = session
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._realm = realm
        self._verify_ssl = verify_ssl
        self._auth: PMGAuth | None = None

    @property
    def base_url(self) -> str:
        return f"https://{self._host}:{self._port}/api2/json"

    def _full_username(self) -> str:
        if "@" in self._username:
            return self._username
        return f"{self._username}@{self._realm}"

    async def async_login(self) -> PMGAuth:
        url = f"{self.base_url}/access/ticket"
        data = {
            "username": self._full_username(),
            "password": self._password,
        }
        ssl_context = False if not self._verify_ssl else None
        try:
            async with self._session.post(url, data=data, ssl=ssl_context) as resp:
                payload = await resp.json()
                if resp.status != 200:
                    raise PMGApiError(f"Login failed: {resp.status} {payload}")
        except (ClientError, ContentTypeError, asyncio.TimeoutError) as err:
            raise PMGApiError(f"Login failed: {err}") from err

        auth_data = payload.get("data") or {}
        ticket = auth_data.get("ticket")
        if not ticket:
            raise PMGApiError("Login failed: missing ticket")

        self._auth = PMGAuth(ticket=ticket, csrf=auth_data.get("CSRFPreventionToken"))
        return self._auth

    async def async_get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        if self._auth is None:
            await self.async_login()

        url = f"{self.base_url}{path}"
        headers = {}
        cookies = {COOKIE_NAME: self._auth.ticket} if self._auth else None

        ssl_context = False if not self._verify_ssl else None
        try:
            async with self._session.get(
                url,
                params=params,
                cookies=cookies,
                ssl=ssl_context,
            ) as resp:
                if resp.status == 401:
                    await self.async_login()
                    cookies = {COOKIE_NAME: self._auth.ticket} if self._auth else None
                    ssl_context = False if not self._verify_ssl else None
                    async with self._session.get(
                        url,
                        params=params,
                        cookies=cookies,
                        ssl=ssl_context,
                    ) as retry_resp:
                        payload = await retry_resp.json()
                        if retry_resp.status != 200:
                            raise PMGApiError(
                                f"GET {path} failed: {retry_resp.status} {payload}"
                            )
                        return payload.get("data")

                payload = await resp.json()
                if resp.status != 200:
                    raise PMGApiError(f"GET {path} failed: {resp.status} {payload}")
        except (ClientError, ContentTypeError, asyncio.TimeoutError) as err:
            raise PMGApiError(f"GET {path} failed: {err}") from err

        return payload.get("data")
