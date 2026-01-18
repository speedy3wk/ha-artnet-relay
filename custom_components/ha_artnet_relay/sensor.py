"""Sensors for relay diagnostics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import ArtNetRelayCoordinator
from .const import DOMAIN


@dataclass(frozen=True)
class RelaySensorDescription:
    key: str
    name: str
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = None


SENSORS: tuple[RelaySensorDescription, ...] = (
    RelaySensorDescription(
        key="packet_count",
        name="Packets relayed",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RelaySensorDescription(
        key="error_count",
        name="Relay errors",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RelaySensorDescription(
        key="last_packet",
        name="Last packet",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    RelaySensorDescription(
        key="targets",
        name="Targets",
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: ArtNetRelayCoordinator = data["coordinator"]
    async_add_entities(
        [RelaySensor(coordinator, entry, description) for description in SENSORS]
    )


class RelaySensor(CoordinatorEntity[ArtNetRelayCoordinator], SensorEntity):
    """Sensor for relay diagnostics."""

    def __init__(
        self,
        coordinator: ArtNetRelayCoordinator,
        entry: ConfigEntry,
        description: RelaySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_class = description.device_class
        self._attr_state_class = description.state_class

    @property
    def native_value(self) -> Any:
        return self.coordinator.data.get(self.entity_description.key)

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.title,
            manufacturer="Custom",
            model="Artnet Relay",
        )
