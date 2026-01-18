import importlib

import voluptuous as vol


def _load_module():
    return importlib.import_module("ha_artnet_relay.config_flow")


def test_validate_targets_invalid():
    module = _load_module()
    data = {"targets": ["not-a-dict"]}
    errors = module._validate_user_input(data)
    assert errors.get("base") == "invalid_targets"

    data = {"targets": "1.2.3.4:99999"}
    errors = module._validate_user_input(data)
    assert errors.get("base") == "invalid_targets"


def test_validate_sources_invalid():
    module = _load_module()
    data = {"allow_sources": [1, 2]}
    errors = module._validate_user_input(data)
    assert errors.get("base") == "invalid_sources"


def test_validate_artnet_filters_invalid():
    module = _load_module()
    data = {"artnet_universe": "16"}
    errors = module._validate_user_input(data)
    assert errors.get("base") == "invalid_artnet_universe"


def test_validate_opcodes_invalid():
    module = _load_module()
    data = {"artnet_opcodes": ["invalid"]}
    errors = module._validate_user_input(data)
    assert errors.get("base") == "invalid_artnet_opcodes"


def test_validate_rate_limit_invalid():
    module = _load_module()
    data = {"rate_limit_pps": -1}
    errors = module._validate_user_input(data)
    assert errors.get("base") == "invalid_rate_limit"


def test_setup_schema_accepts_minimal_required_fields() -> None:
    module = _load_module()
    flow = module.ArtNetRelayConfigFlow()
    schema = flow._get_setup_schema()
    minimal = {
        "basic": {
            "protocol": "artnet",
            "listen_ip": "0.0.0.0",
            "listen_port": 6454,
        },
        "targets": {
            "broadcast_ip": "2.255.255.255",
            "broadcast_port": 6454,
            "broadcast_bind_ip": "2.0.1.1",
        },
    }
    schema(minimal)


def _extract_required_optional(schema: vol.Schema) -> dict[str, dict[str, set[str]]]:
    result: dict[str, dict[str, set[str]]] = {}
    for section_key, section_schema in schema.schema.items():
        section_name = section_key.schema
        required: set[str] = set()
        optional: set[str] = set()
        for field_key in section_schema.schema.keys():
            if isinstance(field_key, vol.Required):
                required.add(field_key.schema)
            elif isinstance(field_key, vol.Optional):
                optional.add(field_key.schema)
        result[section_name] = {"required": required, "optional": optional}
    return result


def test_setup_schema_required_optional_snapshot() -> None:
    module = _load_module()
    flow = module.ArtNetRelayConfigFlow()
    schema = flow._get_setup_schema()
    extracted = _extract_required_optional(schema)

    expected = {
        "basic": {
            "required": {
                module.CONF_PROTOCOL,
                module.CONF_LISTEN_IP,
                module.CONF_LISTEN_PORT,
            },
            "optional": {module.CONF_LISTEN_INTERFACE},
        },
        "targets": {
            "required": {
                module.CONF_BROADCAST_IP,
                module.CONF_BROADCAST_PORT,
                module.CONF_BROADCAST_BIND_IP,
            },
            "optional": {
                module.CONF_NETWORK_INTERFACE,
                module.CONF_SOURCE_PORT,
                module.CONF_AUTO_ADD_BIND_IP,
                module.CONF_BIND_NETMASK,
                module.CONF_TARGETS,
            },
        },
        "filters": {
            "required": set(),
            "optional": {
                module.CONF_ALLOW_SOURCES,
                module.CONF_DENY_SOURCES,
                module.CONF_ARTNET_UNIVERSE,
                module.CONF_ARTNET_SUBNET,
                module.CONF_ARTNET_NET,
            },
        },
        "advanced": {
            "required": set(),
            "optional": {module.CONF_RATE_LIMIT_PPS, module.CONF_ARTNET_OPCODES},
        },
    }

    assert extracted == expected


def test_flatten_sections_merges_values() -> None:
    module = _load_module()
    user_input = {
        "basic": {"protocol": "artnet", "listen_ip": "0.0.0.0", "listen_port": 6454},
        "targets": {"network_interface": ""},
        "filters": {"allow_sources": ""},
        "advanced": {"rate_limit_pps": 0},
    }
    flattened = module._flatten_sections(user_input)
    assert flattened["protocol"] == "artnet"
    assert flattened["network_interface"] == ""
    assert flattened["rate_limit_pps"] == 0


def test_validate_text_filters_valid():
    module = _load_module()
    data = {
        "allow_sources": "1.1.1.1,2.2.2.2",
        "deny_sources": "",
        "artnet_universe": "1,2",
        "artnet_subnet": "0",
        "artnet_net": "7",
    }
    errors = module._validate_user_input(data)
    assert errors == {}
