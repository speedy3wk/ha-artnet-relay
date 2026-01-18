"""Config flow for ArtNet Relay integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.data_entry_flow import section
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
    _data: dict[str, Any] | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            flat_input = _flatten_sections(user_input)
            errors = _validate_user_input(flat_input)
            if errors:
                return self.async_show_form(
                    step_id="user",
                    data_schema=self._get_setup_schema(user_input),
                    errors=errors,
                )
            self._data = flat_input
            await self.async_set_unique_id(
                f"{self._data[CONF_LISTEN_IP]}:{self._data[CONF_LISTEN_PORT]}"
            )
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"ArtNet Relay ({self._data[CONF_LISTEN_IP]}:{self._data[CONF_LISTEN_PORT]})",
                data=self._data,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=self._get_setup_schema(),
            errors=errors,
        )

    def _get_setup_schema(self, defaults: dict[str, Any] | None = None) -> vol.Schema:
        current = _flatten_sections(defaults or {})
        targets_text = _targets_to_text(current.get(CONF_TARGETS, []))
        protocol = current.get(CONF_PROTOCOL, DEFAULT_PROTOCOL)
        allow_sources = _list_to_text(current.get(CONF_ALLOW_SOURCES, ""))
        deny_sources = _list_to_text(current.get(CONF_DENY_SOURCES, ""))
        artnet_universe = _list_to_text(current.get(CONF_ARTNET_UNIVERSE, ""))
        artnet_subnet = _list_to_text(current.get(CONF_ARTNET_SUBNET, ""))
        artnet_net = _list_to_text(current.get(CONF_ARTNET_NET, ""))
        return vol.Schema(
            {
                vol.Required("basic"): section(
                    vol.Schema(
                        {
                            vol.Required(
                                CONF_PROTOCOL,
                                default=current.get(CONF_PROTOCOL, DEFAULT_PROTOCOL),
                            ): vol.In(PROTOCOLS),
                            vol.Required(
                                CONF_LISTEN_IP,
                                default=current.get(CONF_LISTEN_IP, DEFAULT_LISTEN_IP),
                            ): selector.TextSelector(),
                            vol.Required(
                                CONF_LISTEN_PORT,
                                default=current.get(CONF_LISTEN_PORT, DEFAULT_LISTEN_PORT),
                            ): selector.NumberSelector(
                                selector.NumberSelectorConfig(
                                    min=1, max=65535, mode=selector.NumberSelectorMode.BOX
                                )
                            ),
                            vol.Optional(
                                CONF_LISTEN_INTERFACE,
                                default=current.get(
                                    CONF_LISTEN_INTERFACE, DEFAULT_LISTEN_INTERFACE
                                ),
                            ): selector.TextSelector(),
                        }
                    ),
                    {"collapsed": False},
                ),
                vol.Required("targets"): section(
                    vol.Schema(
                        {
                            vol.Required(
                                CONF_BROADCAST_IP,
                                default=current.get(
                                    CONF_BROADCAST_IP, DEFAULT_BROADCAST_IP
                                ),
                            ): selector.TextSelector(),
                            vol.Required(
                                CONF_BROADCAST_PORT,
                                default=current.get(
                                    CONF_BROADCAST_PORT, DEFAULT_BROADCAST_PORT
                                ),
                            ): selector.NumberSelector(
                                selector.NumberSelectorConfig(
                                    min=1, max=65535, mode=selector.NumberSelectorMode.BOX
                                )
                            ),
                            vol.Required(
                                CONF_BROADCAST_BIND_IP,
                                default=current.get(
                                    CONF_BROADCAST_BIND_IP, DEFAULT_BROADCAST_BIND_IP
                                ),
                            ): selector.TextSelector(),
                            vol.Optional(
                                CONF_NETWORK_INTERFACE,
                                default=current.get(
                                    CONF_NETWORK_INTERFACE, DEFAULT_NETWORK_INTERFACE
                                ),
                            ): selector.TextSelector(),
                            vol.Optional(
                                CONF_SOURCE_PORT,
                                default=current.get(
                                    CONF_SOURCE_PORT, DEFAULT_SOURCE_PORT
                                ),
                            ): selector.NumberSelector(
                                selector.NumberSelectorConfig(
                                    min=0, max=65535, mode=selector.NumberSelectorMode.BOX
                                )
                            ),
                            vol.Optional(
                                CONF_AUTO_ADD_BIND_IP,
                                default=current.get(
                                    CONF_AUTO_ADD_BIND_IP, DEFAULT_AUTO_ADD_BIND_IP
                                ),
                            ): selector.BooleanSelector(),
                            vol.Optional(
                                CONF_BIND_NETMASK,
                                default=current.get(CONF_BIND_NETMASK, DEFAULT_BIND_NETMASK),
                            ): selector.NumberSelector(
                                selector.NumberSelectorConfig(
                                    min=0, max=32, mode=selector.NumberSelectorMode.BOX
                                )
                            ),
                            vol.Optional(
                                CONF_TARGETS, default=targets_text
                            ): selector.TextSelector(
                                selector.TextSelectorConfig(multiline=True)
                            ),
                        }
                    ),
                    {"collapsed": False},
                ),
                vol.Optional("filters"): section(
                    vol.Schema(
                        {
                            vol.Optional(
                                CONF_ALLOW_SOURCES,
                                default=allow_sources,
                            ): selector.TextSelector(
                                selector.TextSelectorConfig(multiline=True)
                            ),
                            vol.Optional(
                                CONF_DENY_SOURCES,
                                default=deny_sources,
                            ): selector.TextSelector(
                                selector.TextSelectorConfig(multiline=True)
                            ),
                            **(
                                {
                                    vol.Optional(
                                        CONF_ARTNET_UNIVERSE,
                                        default=artnet_universe,
                                    ): selector.TextSelector(
                                        selector.TextSelectorConfig(multiline=True)
                                    ),
                                    vol.Optional(
                                        CONF_ARTNET_SUBNET,
                                        default=artnet_subnet,
                                    ): selector.TextSelector(
                                        selector.TextSelectorConfig(multiline=True)
                                    ),
                                    vol.Optional(
                                        CONF_ARTNET_NET,
                                        default=artnet_net,
                                    ): selector.TextSelector(
                                        selector.TextSelectorConfig(multiline=True)
                                    ),
                                }
                                if protocol == DEFAULT_PROTOCOL
                                else {}
                            ),
                        }
                    ),
                    {"collapsed": True},
                ),
                vol.Optional("advanced"): section(
                    vol.Schema(
                        {
                            vol.Optional(
                                CONF_RATE_LIMIT_PPS,
                                default=current.get(
                                    CONF_RATE_LIMIT_PPS, DEFAULT_RATE_LIMIT_PPS
                                ),
                            ): selector.NumberSelector(
                                selector.NumberSelectorConfig(
                                    min=0, mode=selector.NumberSelectorMode.BOX
                                )
                            ),
                            **(
                                {
                                    vol.Optional(
                                        CONF_ARTNET_OPCODES,
                                        default=current.get(
                                            CONF_ARTNET_OPCODES, DEFAULT_ARTNET_OPCODES
                                        ),
                                    ): selector.SelectSelector(
                                        selector.SelectSelectorConfig(
                                            options=ARTNET_OPCODES,
                                            multiple=True,
                                        )
                                    )
                                }
                                if protocol == DEFAULT_PROTOCOL
                                else {}
                            ),
                        }
                    ),
                    {"collapsed": True},
                ),
            }
        )


def _list_to_text(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    if isinstance(value, str):
        return value
    return ""


def _targets_to_text(value: Any) -> str:
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if not isinstance(item, dict):
                continue
            host = str(item.get("host", "")).strip()
            port = int(item.get("port", 0)) if item.get("port") is not None else 0
            if host and port:
                parts.append(f"{host}:{port}")
            elif host:
                parts.append(host)
        return ", ".join(parts)
    if isinstance(value, str):
        return value
    return ""


def _flatten_sections(user_input: dict[str, Any]) -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    for key, value in user_input.items():
        if key in ("basic", "targets", "filters", "advanced") and isinstance(value, dict):
            flattened.update(value)
        else:
            flattened[key] = value
    return flattened


class ArtNetRelayOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle ArtNet Relay options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry
        self._options: dict[str, Any] = {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            flat_input = _flatten_sections(user_input)
            errors = _validate_user_input(flat_input)
            if errors:
                return self.async_show_form(
                    step_id="init",
                    data_schema=ArtNetRelayConfigFlow._get_setup_schema(self, user_input),
                    errors=errors,
                )
            self._options = flat_input
            return self.async_create_entry(title="", data=self._options)

        current = {**self._config_entry.data, **self._config_entry.options}

        return self.async_show_form(
            step_id="init",
            data_schema=ArtNetRelayConfigFlow._get_setup_schema(self, current),
        )


def _validate_user_input(user_input: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}

    targets = user_input.get(CONF_TARGETS, [])
    if targets:
        if isinstance(targets, list):
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
        elif isinstance(targets, str):
            parts = [p.strip() for p in targets.replace("\n", ",").split(",")]
            for part in parts:
                if not part:
                    continue
                if ":" in part:
                    host, port_text = part.split(":", 1)
                    if not host.strip():
                        errors["base"] = "invalid_targets"
                        return errors
                    try:
                        port = int(port_text)
                    except ValueError:
                        errors["base"] = "invalid_targets"
                        return errors
                    if not (1 <= port <= 65535):
                        errors["base"] = "invalid_targets"
                        return errors
                else:
                    if not part.strip():
                        errors["base"] = "invalid_targets"
                        return errors
        else:
            errors["base"] = "invalid_targets"
            return errors

    for key in (CONF_ALLOW_SOURCES, CONF_DENY_SOURCES):
        value = user_input.get(key, "")
        if isinstance(value, list):
            if any(not isinstance(v, str) for v in value):
                errors["base"] = "invalid_sources"
                return errors
        elif isinstance(value, str):
            pass
        else:
            errors["base"] = "invalid_sources"
            return errors

    for key, max_value, error_key in (
        (CONF_ARTNET_UNIVERSE, 15, "invalid_artnet_universe"),
        (CONF_ARTNET_SUBNET, 15, "invalid_artnet_subnet"),
        (CONF_ARTNET_NET, 127, "invalid_artnet_net"),
    ):
        value = user_input.get(key, "")
        if not value:
            continue
        items: list[int] = []
        if isinstance(value, list):
            for item in value:
                if not isinstance(item, int) or not (0 <= item <= max_value):
                    errors["base"] = error_key
                    return errors
                items.append(item)
        elif isinstance(value, str):
            parts = [p.strip() for p in value.replace("\n", ",").split(",")]
            for part in parts:
                if not part:
                    continue
                try:
                    num = int(part)
                except ValueError:
                    errors["base"] = error_key
                    return errors
                if not (0 <= num <= max_value):
                    errors["base"] = error_key
                    return errors
                items.append(num)
        else:
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
        if not isinstance(rate_limit, (int, float)) or rate_limit < 0:
            errors["base"] = "invalid_rate_limit"
            return errors

    return errors
