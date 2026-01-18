"""Data update coordinator for relay diagnostics."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class ArtNetRelayCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for relay stats."""

    def __init__(self, hass: HomeAssistant, relay: Any) -> None:
        self.relay = relay
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_stats",
            update_interval=timedelta(seconds=10),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        return self.relay.stats
