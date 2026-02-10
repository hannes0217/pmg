"""Buttons for Proxmox Mail Gateway."""

from __future__ import annotations

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import CONF_HOST

from . import PMGDataUpdateCoordinator
from .api import PMGApiError
from .const import ATTRIBUTION, DOMAIN, SERVICE_REBOOT, SERVICE_SHUTDOWN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PMGDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[ButtonEntity] = []
    nodes = coordinator.data.get("nodes", {}) if coordinator.data else {}
    for node_name in nodes:
        entities.append(PMGNodeRebootButton(coordinator, entry, node_name))
        entities.append(PMGNodeShutdownButton(coordinator, entry, node_name))

    async_add_entities(entities)


class _PMGNodeButton(CoordinatorEntity[PMGDataUpdateCoordinator], ButtonEntity):
    def __init__(
        self,
        coordinator: PMGDataUpdateCoordinator,
        entry: ConfigEntry,
        node_name: str,
        command: str,
        name: str,
        device_class: ButtonDeviceClass | None,
    ) -> None:
        super().__init__(coordinator)
        self._node_name = node_name
        self._command = command
        self._attr_name = name
        self._attr_device_class = device_class
        self._attr_unique_id = (
            f"{entry.entry_id}_v2_{entry.data[CONF_HOST]}_{node_name}_{command}"
        )
        self._attr_suggested_object_id = (
            f"pmg_{entry.data[CONF_HOST]}_{node_name}_{command}"
        )
        self._attr_attribution = ATTRIBUTION
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.data[CONF_HOST]}-{node_name}")},
            name=f"{entry.data[CONF_HOST]} ({node_name})",
            manufacturer="Proxmox",
            model="Proxmox Mail Gateway",
        )

    async def async_press(self) -> None:
        try:
            await self.coordinator.client.async_post(
                f"/nodes/{self._node_name}/status",
                data={"command": self._command},
            )
        except PMGApiError as err:
            raise RuntimeError(str(err)) from err


class PMGNodeRebootButton(_PMGNodeButton):
    def __init__(
        self, coordinator: PMGDataUpdateCoordinator, entry: ConfigEntry, node_name: str
    ) -> None:
        super().__init__(
            coordinator=coordinator,
            entry=entry,
            node_name=node_name,
            command=SERVICE_REBOOT,
            name="Reboot",
            device_class=ButtonDeviceClass.RESTART,
        )


class PMGNodeShutdownButton(_PMGNodeButton):
    def __init__(
        self, coordinator: PMGDataUpdateCoordinator, entry: ConfigEntry, node_name: str
    ) -> None:
        super().__init__(
            coordinator=coordinator,
            entry=entry,
            node_name=node_name,
            command=SERVICE_SHUTDOWN,
            name="Shutdown",
            device_class=ButtonDeviceClass.SHUTDOWN,
        )
