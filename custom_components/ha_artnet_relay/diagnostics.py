"""Diagnostics support for ArtNet Relay."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.loader import async_get_integration

from .const import DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    data = hass.data[DOMAIN][entry.entry_id]
    relay = data["relay"]
    coordinator = data["coordinator"]

    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)
    device = device_registry.async_get_device(identifiers={(DOMAIN, entry.entry_id)})
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    integration = await async_get_integration(hass, DOMAIN)

    return {
        "entry": {
            "entry_id": entry.entry_id,
            "title": entry.title,
            "data": entry.data,
            "options": entry.options,
        },
        "device": device.as_dict() if device else None,
        "integration": {
            "version": integration.version,
            "name": integration.name,
        },
        "entities": [entity.as_dict() for entity in entities],
        "stats": relay.stats,
        "coordinator": coordinator.data,
    }
