"""Sensors for Proxmox Mail Gateway."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
    PERCENTAGE,
    UnitOfInformation,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import CONF_HOST

from . import PMGDataUpdateCoordinator
from .const import ATTRIBUTION, DOMAIN


@dataclass(frozen=True, kw_only=True)
class PMGNodeSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any] | None = None
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = None


@dataclass(frozen=True, kw_only=True)
class PMGStatsSensorDescription(SensorEntityDescription):
    key: str
    native_unit_of_measurement: str | None = None
    value_fn: Callable[[Any], Any] | None = None
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = None


NODE_SENSORS: tuple[PMGNodeSensorDescription, ...] = (
    PMGNodeSensorDescription(
        key="cpu_usage",
        name="CPU Usage",
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: round((data.get("cpu") or 0) * 100, 1)
        if data.get("cpu") is not None
        else None,
    ),
    PMGNodeSensorDescription(
        key="loadavg_1m",
        name="Load Average (1m)",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: (data.get("loadavg") or [None])[0],
    ),
    PMGNodeSensorDescription(
        key="memory_used",
        name="Memory Used",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("mem")
        or (data.get("memory") or {}).get("used")
        or (data.get("memory") or {}).get("usage"),
    ),
    PMGNodeSensorDescription(
        key="memory_total",
        name="Memory Total",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("maxmem")
        or (data.get("memory") or {}).get("total")
        or (data.get("memory") or {}).get("size"),
    ),
    PMGNodeSensorDescription(
        key="disk_used",
        name="Disk Used",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("disk") or (data.get("rootfs") or {}).get("used"),
    ),
    PMGNodeSensorDescription(
        key="disk_total",
        name="Disk Total",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("maxdisk")
        or (data.get("rootfs") or {}).get("total"),
    ),
    PMGNodeSensorDescription(
        key="uptime",
        name="Uptime",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: round((data.get("uptime") or 0) / 3600, 2)
        if data.get("uptime") is not None
        else None,
    ),
)


STATS_SENSORS: tuple[PMGStatsSensorDescription, ...] = (
    PMGStatsSensorDescription(
        key="count", name="Mail Total", state_class=SensorStateClass.MEASUREMENT
    ),
    PMGStatsSensorDescription(
        key="count_in", name="Mail In", state_class=SensorStateClass.MEASUREMENT
    ),
    PMGStatsSensorDescription(
        key="count_out", name="Mail Out", state_class=SensorStateClass.MEASUREMENT
    ),
    PMGStatsSensorDescription(
        key="junk_in", name="Junk In", state_class=SensorStateClass.MEASUREMENT
    ),
    PMGStatsSensorDescription(
        key="junk_out", name="Junk Out", state_class=SensorStateClass.MEASUREMENT
    ),
    PMGStatsSensorDescription(
        key="spamcount_in", name="Spam In", state_class=SensorStateClass.MEASUREMENT
    ),
    PMGStatsSensorDescription(
        key="spamcount_out", name="Spam Out", state_class=SensorStateClass.MEASUREMENT
    ),
    PMGStatsSensorDescription(
        key="viruscount_in", name="Virus In", state_class=SensorStateClass.MEASUREMENT
    ),
    PMGStatsSensorDescription(
        key="viruscount_out", name="Virus Out", state_class=SensorStateClass.MEASUREMENT
    ),
    PMGStatsSensorDescription(
        key="bounces_in", name="Bounces In", state_class=SensorStateClass.MEASUREMENT
    ),
    PMGStatsSensorDescription(
        key="bounces_out", name="Bounces Out", state_class=SensorStateClass.MEASUREMENT
    ),
    PMGStatsSensorDescription(
        key="bytes_in",
        name="Bytes In",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    PMGStatsSensorDescription(
        key="bytes_out",
        name="Bytes Out",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    PMGStatsSensorDescription(
        key="avptime",
        name="AVP Time",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        value_fn=lambda v: round(float(v), 3) if v is not None else None,
    ),
    PMGStatsSensorDescription(
        key="glcount", name="Greylist", state_class=SensorStateClass.MEASUREMENT
    ),
    PMGStatsSensorDescription(
        key="pregreet_rejects",
        name="Pregreet Rejects",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    PMGStatsSensorDescription(
        key="rbl_rejects", name="RBL Rejects", state_class=SensorStateClass.MEASUREMENT
    ),
    PMGStatsSensorDescription(
        key="spfcount", name="SPF Rejects", state_class=SensorStateClass.MEASUREMENT
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PMGDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    nodes = coordinator.data.get("nodes", {}) if coordinator.data else {}
    for node_name in nodes:
        for description in NODE_SENSORS:
            entities.append(PMGNodeSensor(coordinator, entry, node_name, description))

    for description in STATS_SENSORS:
        entities.append(PMGMailStatsSensor(coordinator, entry, description))

    entities.append(PMGVersionSensor(coordinator, entry))

    async_add_entities(entities)


class PMGNodeSensor(CoordinatorEntity[PMGDataUpdateCoordinator], SensorEntity):
    """Node sensor."""

    def __init__(
        self,
        coordinator: PMGDataUpdateCoordinator,
        entry: ConfigEntry,
        node_name: str,
        description: PMGNodeSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._node_name = node_name
        self._attr_unique_id = f"{entry.entry_id}_{node_name}_{description.key}"
        self._attr_name = f"PMG {entry.data[CONF_HOST]} {node_name} {description.name}"
        self._attr_suggested_object_id = (
            f"pmg_{entry.data[CONF_HOST]}_{node_name}_{description.key}"
        )
        self._attr_attribution = ATTRIBUTION
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.data[CONF_HOST]}-{node_name}")},
            name=f"{entry.data[CONF_HOST]} ({node_name})",
            manufacturer="Proxmox",
            model="Proxmox Mail Gateway",
        )

    @property
    def native_value(self):
        node_data = (self.coordinator.data or {}).get("nodes", {}).get(self._node_name, {})
        value_fn = self.entity_description.value_fn
        if value_fn is None:
            return None
        return value_fn(node_data)


class PMGMailStatsSensor(CoordinatorEntity[PMGDataUpdateCoordinator], SensorEntity):
    """Mail statistics sensor."""

    def __init__(
        self,
        coordinator: PMGDataUpdateCoordinator,
        entry: ConfigEntry,
        description: PMGStatsSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = SensorEntityDescription(
            key=description.key,
            name=description.name,
            native_unit_of_measurement=description.native_unit_of_measurement,
            device_class=description.device_class,
            state_class=description.state_class,
        )
        self._key = description.key
        self._value_fn = description.value_fn
        self._attr_unique_id = f"{entry.entry_id}_mail_{description.key}"
        self._attr_name = f"PMG {entry.data[CONF_HOST]} {description.name}"
        self._attr_suggested_object_id = f"pmg_{entry.data[CONF_HOST]}_{description.key}"
        self._attr_attribution = ATTRIBUTION
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data[CONF_HOST])},
            name=entry.data[CONF_HOST],
            manufacturer="Proxmox",
            model="Proxmox Mail Gateway",
        )

    @property
    def native_value(self):
        stats = (self.coordinator.data or {}).get("mail_stats") or {}
        value = _extract_stat(stats, self._key)
        if self._value_fn is not None:
            return self._value_fn(value)
        return value


class PMGVersionSensor(CoordinatorEntity[PMGDataUpdateCoordinator], SensorEntity):
    """Version sensor."""

    _attr_name = "PMG Version"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: PMGDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_version"
        self._attr_attribution = ATTRIBUTION
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data[CONF_HOST])},
            name=entry.data[CONF_HOST],
            manufacturer="Proxmox",
            model="Proxmox Mail Gateway",
        )

    @property
    def native_value(self):
        version = (self.coordinator.data or {}).get("version") or {}
        return version.get("version") or version.get("release")


def _extract_stat(stats: Any, key: str) -> Any:
    if isinstance(stats, dict):
        if key in stats:
            return stats[key]
        data = stats.get("data")
        if isinstance(data, dict):
            return data.get(key)
        if isinstance(data, list):
            return _sum_stat_list(data, key)

    if isinstance(stats, list):
        return _sum_stat_list(stats, key)

    return None


def _sum_stat_list(items: list[dict[str, Any]], key: str) -> Any:
    total = 0
    found = False
    for item in items:
        if key in item and isinstance(item[key], (int, float)):
            total += item[key]
            found = True
    return total if found else None
