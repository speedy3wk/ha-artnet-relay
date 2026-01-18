import asyncio
import importlib
from pathlib import Path


def _load_module():
    return importlib.import_module("ha_artnet_relay")


def test_parse_targets_list_only():
    module = _load_module()
    targets = module._parse_targets(
        [{"host": "2.255.255.255", "port": 6454}, {"host": "10.0.0.255"}],
        6454,
    )
    assert len(targets) == 2
    assert targets[0].host == "2.255.255.255"
    assert targets[0].port == 6454
    assert targets[1].host == "10.0.0.255"
    assert targets[1].port == 6454

    targets = module._parse_targets("2.255.255.255:6454\n10.0.0.255", 6454)
    assert len(targets) == 2
    assert targets[0].host == "2.255.255.255"
    assert targets[0].port == 6454


def test_parse_ip_list_only_list():
    module = _load_module()
    assert module._parse_ip_list(["1.2.3.4", " 5.6.7.8 "]) == ["1.2.3.4", "5.6.7.8"]
    assert module._parse_ip_list("1.2.3.4, 9.9.9.9") == ["1.2.3.4", "9.9.9.9"]


def test_parse_int_list_only_list():
    module = _load_module()
    assert module._parse_int_list([0, 15, "7", None]) == [0, 15, 7]
    assert module._parse_int_list("1, 2") == [1, 2]


def test_parse_str_list_only_list():
    module = _load_module()
    assert module._parse_str_list(["artdmx", " artsync "]) == ["artdmx", "artsync"]
    assert module._parse_str_list("artdmx") == []


def test_extract_artnet_fields_artdmx():
    module = _load_module()
    data = bytearray(18)
    data[0:8] = b"Art-Net\x00"
    data[8:10] = b"\x00\x50"  # ArtDMX
    data[14] = 0x2F  # subnet=2, universe=15
    data[15] = 0x07  # net=7
    fields = module._extract_artnet_fields(bytes(data))
    assert fields == (7, 2, 15)


def test_get_artnet_opcode():
    module = _load_module()
    data = b"Art-Net\x00\x00\x52" + b"\x00" * 10
    assert module._get_artnet_opcode(data) == b"\x00\x52"


def test_rate_limiter():
    module = _load_module()

    async def _run():
        limiter = module.RateLimiter(2)
        assert limiter.allow() is True
        assert limiter.allow() is True
        assert limiter.allow() is False

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_run())
    finally:
        loop.close()
