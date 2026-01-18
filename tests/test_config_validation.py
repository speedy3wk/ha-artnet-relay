import importlib


def _load_module():
    return importlib.import_module("ha_artnet_relay.config_flow")


def test_validate_targets_invalid():
    module = _load_module()
    data = {"targets": ["not-a-dict"]}
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
