"""Config flow for ArtNet Relay integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_AUTO_ADD_BIND_IP,
    CONF_ALLOW_SOURCES,
    CONF_ARTNET_NET,
    CONF_ARTNET_OPCODES,
    CONF_ARTNET_SUBNET,
    CONF_ARTNET_UNIVERSE,
    CONF_BROADCAST_BIND_IP,
    CONF_BROADCAST_IP,
    CONF_BROADCAST_PORT,
    CONF_BIND_NETMASK,
    CONF_DENY_SOURCES,
    CONF_LISTEN_IP,
    CONF_LISTEN_INTERFACE,
    CONF_LISTEN_PORT,
    CONF_NETWORK_INTERFACE,
    CONF_PROTOCOL,
    CONF_RATE_LIMIT_PPS,
    CONF_SOURCE_PORT,
    CONF_TARGETS,
    DEFAULT_AUTO_ADD_BIND_IP,
    DEFAULT_ALLOW_SOURCES,
    DEFAULT_ARTNET_NET,
    DEFAULT_ARTNET_OPCODES,
    DEFAULT_ARTNET_SUBNET,
    DEFAULT_ARTNET_UNIVERSE,
    DEFAULT_BROADCAST_BIND_IP,
    DEFAULT_BROADCAST_IP,
    DEFAULT_BROADCAST_PORT,
    DEFAULT_BIND_NETMASK,
    DEFAULT_DENY_SOURCES,
    DEFAULT_LISTEN_IP,
    DEFAULT_LISTEN_INTERFACE,
    DEFAULT_LISTEN_PORT,
    DEFAULT_NETWORK_INTERFACE,
    DEFAULT_PROTOCOL,
    DEFAULT_RATE_LIMIT_PPS,
    ARTNET_OPCODES,
    DEFAULT_SOURCE_PORT,
    DOMAIN,
    PROTOCOLS,
)


class ArtNetRelayConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ArtNet Relay."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = _validate_user_input(user_input)
            if errors:
                return self.async_show_form(
                    step_id="user",
                    data_schema=self._get_data_schema(user_input),
                    errors=errors,
                )
            # Validate IPs are valid format
            await self.async_set_unique_id(
                f"{user_input[CONF_LISTEN_IP]}:{user_input[CONF_LISTEN_PORT]}"
            )
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"ArtNet Relay ({user_input[CONF_LISTEN_IP]}:{user_input[CONF_LISTEN_PORT]} → {user_input[CONF_BROADCAST_IP]})",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=self._get_data_schema(),
            errors=errors,
        )

    def _get_data_schema(self, defaults: dict[str, Any] | None = None) -> vol.Schema:
        current = defaults or {}
        return vol.Schema(
            {
                vol.Required(
                    CONF_PROTOCOL, default=current.get(CONF_PROTOCOL, DEFAULT_PROTOCOL)
                ): vol.In(PROTOCOLS),
                vol.Required(
                    CONF_LISTEN_IP, default=current.get(CONF_LISTEN_IP, DEFAULT_LISTEN_IP)
                ): str,
                vol.Required(
                    CONF_LISTEN_PORT,
                    default=current.get(CONF_LISTEN_PORT, DEFAULT_LISTEN_PORT),
                ): int,
                vol.Optional(
                    CONF_LISTEN_INTERFACE,
                    default=current.get(CONF_LISTEN_INTERFACE, DEFAULT_LISTEN_INTERFACE),
                ): str,
                vol.Required(
                    CONF_BROADCAST_IP,
                    default=current.get(CONF_BROADCAST_IP, DEFAULT_BROADCAST_IP),
                ): str,
                vol.Required(
                    CONF_BROADCAST_PORT,
                    default=current.get(CONF_BROADCAST_PORT, DEFAULT_BROADCAST_PORT),
                ): int,
                vol.Required(
                    CONF_BROADCAST_BIND_IP,
                    default=current.get(CONF_BROADCAST_BIND_IP, DEFAULT_BROADCAST_BIND_IP),
                ): str,
                vol.Required(
                    CONF_NETWORK_INTERFACE,
                    default=current.get(CONF_NETWORK_INTERFACE, DEFAULT_NETWORK_INTERFACE),
                ): str,
                vol.Optional(
                    CONF_SOURCE_PORT,
                    default=current.get(CONF_SOURCE_PORT, DEFAULT_SOURCE_PORT),
                ): int,
                vol.Optional(
                    CONF_AUTO_ADD_BIND_IP,
                    default=current.get(CONF_AUTO_ADD_BIND_IP, DEFAULT_AUTO_ADD_BIND_IP),
                ): bool,
                vol.Optional(
                    CONF_BIND_NETMASK,
                    default=current.get(CONF_BIND_NETMASK, DEFAULT_BIND_NETMASK),
                ): int,
                vol.Optional(
                    CONF_RATE_LIMIT_PPS,
                    default=current.get(CONF_RATE_LIMIT_PPS, DEFAULT_RATE_LIMIT_PPS),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Optional(
                    CONF_TARGETS, default=current.get(CONF_TARGETS, [])
                ): selector.ObjectSelector(),
                vol.Optional(
                    CONF_ALLOW_SOURCES,
                    default=current.get(CONF_ALLOW_SOURCES, DEFAULT_ALLOW_SOURCES),
                ): selector.ObjectSelector(),
                vol.Optional(
                    CONF_DENY_SOURCES,
                    default=current.get(CONF_DENY_SOURCES, DEFAULT_DENY_SOURCES),
                ): selector.ObjectSelector(),
                vol.Optional(
                    CONF_ARTNET_UNIVERSE,
                    default=current.get(CONF_ARTNET_UNIVERSE, DEFAULT_ARTNET_UNIVERSE),
                ): selector.ObjectSelector(),
                vol.Optional(
                    CONF_ARTNET_SUBNET,
                    default=current.get(CONF_ARTNET_SUBNET, DEFAULT_ARTNET_SUBNET),
                ): selector.ObjectSelector(),
                vol.Optional(
                    CONF_ARTNET_NET,
                    default=current.get(CONF_ARTNET_NET, DEFAULT_ARTNET_NET),
                ): selector.ObjectSelector(),
                vol.Optional(
                    CONF_ARTNET_OPCODES,
                    default=current.get(CONF_ARTNET_OPCODES, DEFAULT_ARTNET_OPCODES),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=ARTNET_OPCODES,
                        multiple=True,
                    )
                ),
            }
        )

    @staticmethod
    @config_entries.callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return ArtNetRelayOptionsFlowHandler(config_entry)


class ArtNetRelayOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle ArtNet Relay options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            errors = _validate_user_input(user_input)
            if errors:
                return self.async_show_form(
                    step_id="init",
                    data_schema=self._get_options_schema(user_input),
                    errors=errors,
                )
            return self.async_create_entry(title="", data=user_input)

        current = {**self._config_entry.data, **self._config_entry.options}

        return self.async_show_form(
            step_id="init",
            data_schema=self._get_options_schema(current),
        )

    def _get_options_schema(self, current: dict[str, Any]) -> vol.Schema:
        return ArtNetRelayConfigFlow._get_data_schema(self, current)


def _validate_user_input(user_input: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}

    targets = user_input.get(CONF_TARGETS, [])
    if targets:
        if not isinstance(targets, list):
            errors["base"] = "invalid_targets"
            return errors
        for item in targets:
            if not isinstance(item, dict):
                errors["base"] = "invalid_targets"
                return errors
            host = item.get("host")
            port = item.get("port")
            if not isinstance(host, str) or not host.strip():
                errors["base"] = "invalid_targets"
                return errors
            if port is None or not isinstance(port, int) or not (1 <= port <= 65535):
                errors["base"] = "invalid_targets"
                return errors

    for key in (CONF_ALLOW_SOURCES, CONF_DENY_SOURCES):
        value = user_input.get(key, [])
        if value and (not isinstance(value, list) or any(not isinstance(v, str) for v in value)):
            errors["base"] = "invalid_sources"
            return errors

    for key, max_value, error_key in (
        (CONF_ARTNET_UNIVERSE, 15, "invalid_artnet_universe"),
        (CONF_ARTNET_SUBNET, 15, "invalid_artnet_subnet"),
        (CONF_ARTNET_NET, 127, "invalid_artnet_net"),
    ):
        value = user_input.get(key, [])
        if value:
            if not isinstance(value, list):
                errors["base"] = error_key
                return errors
            for item in value:
                if not isinstance(item, int) or not (0 <= item <= max_value):
                    errors["base"] = error_key
                    return errors

    opcodes = user_input.get(CONF_ARTNET_OPCODES, DEFAULT_ARTNET_OPCODES)
    if opcodes:
        if not isinstance(opcodes, list) or any(not isinstance(v, str) for v in opcodes):
            errors["base"] = "invalid_artnet_opcodes"
            return errors
        if any(opcode not in ARTNET_OPCODES for opcode in opcodes):
            errors["base"] = "invalid_artnet_opcodes"
            return errors

    rate_limit = user_input.get(CONF_RATE_LIMIT_PPS, DEFAULT_RATE_LIMIT_PPS)
    if rate_limit is not None:
        if not isinstance(rate_limit, int) or rate_limit < 0:
            errors["base"] = "invalid_rate_limit"
            return errors

    return errors
