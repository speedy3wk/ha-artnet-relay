import asyncio
import importlib

from .relay_harness import (
    DummyHass,
    make_artnet_packet,
    reserve_udp_port,
    send_udp_packet,
    start_udp_sink,
    wait_for_relay_socket,
)


def _load_module():
    return importlib.import_module("ha_artnet_relay")


def test_artnet_opcode_filtering_end_to_end():
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

        artsync = make_artnet_packet(b"\x00\x52")
        await send_udp_packet(artsync, "127.0.0.1", listen_port)
        await asyncio.sleep(0.05)
        assert sink.protocol.queue.empty() is True

        artdmx = make_artnet_packet(b"\x00\x50")
        await send_udp_packet(artdmx, "127.0.0.1", listen_port)
        data, _ = await asyncio.wait_for(sink.protocol.queue.get(), timeout=1.0)
        assert data == artdmx

        await relay.stop()
        sink.transport.close()

    asyncio.run(_run())
