import asyncio
import importlib

from .relay_harness import (
    DummyHass,
    make_artnet_dmx_packet,
    reserve_udp_port,
    send_udp_packet,
    start_udp_sink,
    wait_for_relay_socket,
)


def _load_module():
    return importlib.import_module("ha_artnet_relay")


def test_filters_allow_deny_and_universe():
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
            allow_sources=["127.0.0.1"],
            deny_sources=["192.0.2.10"],
            artnet_universe=[1],
            artnet_subnet=[2],
            artnet_net=[3],
            artnet_opcodes=["artdmx"],
            rate_limit_pps=0,
            auto_add_bind_ip=False,
            bind_netmask=0,
        )
        assert await relay.start() is True
        await wait_for_relay_socket(relay)

        packet_ok = make_artnet_dmx_packet(universe=1, subnet=2, net=3)
        await send_udp_packet(packet_ok, "127.0.0.1", listen_port)
        data, _ = await asyncio.wait_for(sink.protocol.queue.get(), timeout=1.0)
        assert data == packet_ok

        packet_bad_universe = make_artnet_dmx_packet(universe=2, subnet=2, net=3)
        await send_udp_packet(packet_bad_universe, "127.0.0.1", listen_port)
        await asyncio.sleep(0.05)
        assert sink.protocol.queue.empty() is True

        await relay.stop()
        sink.transport.close()

    asyncio.run(_run())


def test_rate_limit_drops_packets_end_to_end():
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
            protocol=module.PROTOCOL_UDP,
            allow_sources=[],
            deny_sources=[],
            artnet_universe=[],
            artnet_subnet=[],
            artnet_net=[],
            artnet_opcodes=[],
            rate_limit_pps=1,
            auto_add_bind_ip=False,
            bind_netmask=0,
        )
        assert await relay.start() is True
        await wait_for_relay_socket(relay)

        payload = b"rate"
        await send_udp_packet(payload, "127.0.0.1", listen_port)
        await send_udp_packet(payload, "127.0.0.1", listen_port)

        data, _ = await asyncio.wait_for(sink.protocol.queue.get(), timeout=1.0)
        assert data == payload
        await asyncio.sleep(0.05)
        assert sink.protocol.queue.empty() is True

        await relay.stop()
        sink.transport.close()

    asyncio.run(_run())


def test_filters_deny_sources_blocks():
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
            protocol=module.PROTOCOL_UDP,
            allow_sources=[],
            deny_sources=["127.0.0.1"],
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

        payload = b"blocked"
        await send_udp_packet(payload, "127.0.0.1", listen_port)
        await asyncio.sleep(0.05)
        assert sink.protocol.queue.empty() is True

        await relay.stop()
        sink.transport.close()

    asyncio.run(_run())
