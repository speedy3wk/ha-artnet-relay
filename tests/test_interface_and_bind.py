import asyncio
import importlib

import pytest

from .relay_harness import DummyHass, reserve_udp_port, send_udp_packet, start_udp_sink, wait_for_relay_socket


def _load_module():
    return importlib.import_module("ha_artnet_relay")


def test_listen_interface_ignored_when_unsupported():
    module = _load_module()

    async def _run():
        sink = await start_udp_sink()
        listen_port = reserve_udp_port()
        relay = module.UdpRelay(
            hass=DummyHass(),
            listen_ip="127.0.0.1",
            listen_port=listen_port,
            listen_interface="lo0",
            targets=[module.RelayTarget("127.0.0.1", sink.port)],
            bind_ip="",
            bind_interface="lo0",
            source_port=0,
            protocol=module.PROTOCOL_UDP,
            allow_sources=[],
            deny_sources=[],
            artnet_universe=[],
            artnet_subnet=[],
            artnet_net=[],
            artnet_opcodes=[],
            rate_limit_pps=0,
            auto_add_bind_ip=False,
            bind_netmask=0,
        )
        assert await relay.start() is True
        await wait_for_relay_socket(relay)

        payload = b"iface"
        await send_udp_packet(payload, "127.0.0.1", listen_port)
        data, _ = await asyncio.wait_for(sink.protocol.queue.get(), timeout=1.0)
        assert data == payload

        await relay.stop()
        sink.transport.close()

    asyncio.run(_run())


def test_auto_add_bind_ip_invokes_helper():
    module = _load_module()

    async def _run():
        sink = await start_udp_sink()
        listen_port = reserve_udp_port()
        called = {}

        async def _fake_add_ip(ip, netmask, interface):
            called["args"] = (ip, netmask, interface)
            return True

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(module, "_try_add_ip_address", _fake_add_ip)

        relay = module.UdpRelay(
            hass=DummyHass(),
            listen_ip="127.0.0.1",
            listen_port=listen_port,
            listen_interface="",
            targets=[module.RelayTarget("127.0.0.1", sink.port)],
            bind_ip="2.0.1.1",
            bind_interface="lo",
            source_port=0,
            protocol=module.PROTOCOL_UDP,
            allow_sources=[],
            deny_sources=[],
            artnet_universe=[],
            artnet_subnet=[],
            artnet_net=[],
            artnet_opcodes=[],
            rate_limit_pps=0,
            auto_add_bind_ip=True,
            bind_netmask=24,
        )
        assert await relay.start() is True

        for _ in range(100):
            if called.get("args"):
                break
            await asyncio.sleep(0.01)

        assert called.get("args") == ("2.0.1.1", "24", "lo")

        await relay.stop()
        sink.transport.close()
        monkeypatch.undo()

    asyncio.run(_run())
