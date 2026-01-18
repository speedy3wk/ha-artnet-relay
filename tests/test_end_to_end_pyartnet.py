import asyncio
import importlib

import pytest

from .relay_harness import (
    DummyHass,
    reserve_udp_port,
    start_udp_sink,
    wait_for_datagram,
    wait_for_relay_socket,
)


def _load_module():
    return importlib.import_module("ha_artnet_relay")


def test_pyartnet_artdmx_forwarding():
    pyartnet = pytest.importorskip("pyartnet")
    module = _load_module()

    async def _run():
        sink = await start_udp_sink()
        listen_port = reserve_udp_port()
        relay = module.UdpRelay(
            hass=DummyHass(),
            listen_ip="127.0.0.1",
            listen_port=listen_port,
            listen_interface="",
            targets=[module.RelayTarget("127.0.0.1", sink.port)],
            bind_ip="",
            bind_interface="",
            source_port=0,
            protocol=module.PROTOCOL_ARTNET,
            allow_sources=[],
            deny_sources=[],
            artnet_universe=[],
            artnet_subnet=[],
            artnet_net=[],
            artnet_opcodes=["artdmx"],
            rate_limit_pps=0,
            auto_add_bind_ip=False,
            bind_netmask=0,
        )
        assert await relay.start() is True
        await wait_for_relay_socket(relay)

        async with pyartnet.ArtNetNode.create("127.0.0.1", port=listen_port) as node:
            universe = node.add_universe(0)
            channel = universe.add_channel(start=1, width=3)
            channel.set_values([10, 20, 30])
            await asyncio.sleep(0.05)

        data = await wait_for_datagram(sink.protocol)
        assert data.startswith(b"Art-Net\x00")

        await relay.stop()
        sink.transport.close()

    asyncio.run(_run())
