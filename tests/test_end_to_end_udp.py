import asyncio
import importlib

from .relay_harness import (
    DummyHass,
    make_artnet_dmx_packet,
    reserve_udp_port,
    send_udp_packet,
    start_udp_sink,
    wait_for_datagram,
    wait_for_relay_socket,
)


def _load_module():
    return importlib.import_module("ha_artnet_relay")


def test_udp_artnet_unicast_forwarding():
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

        packet = make_artnet_dmx_packet(universe=1, subnet=2, net=3)
        await send_udp_packet(packet, "127.0.0.1", listen_port)
        data = await wait_for_datagram(sink.protocol)
        assert data == packet

        await relay.stop()
        sink.transport.close()

    asyncio.run(_run())


def test_udp_multiple_targets_forwarding():
    module = _load_module()

    async def _run():
        sink_a = await start_udp_sink()
        sink_b = await start_udp_sink()
        listen_port = reserve_udp_port()
        relay = module.UdpRelay(
            hass=DummyHass(),
            listen_ip="127.0.0.1",
            listen_port=listen_port,
            listen_interface="",
            targets=[
                module.RelayTarget("127.0.0.1", sink_a.port),
                module.RelayTarget("127.0.0.1", sink_b.port),
            ],
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
            rate_limit_pps=0,
            auto_add_bind_ip=False,
            bind_netmask=0,
        )
        assert await relay.start() is True
        await wait_for_relay_socket(relay)

        payload = b"hello"
        await send_udp_packet(payload, "127.0.0.1", listen_port)
        data_a = await wait_for_datagram(sink_a.protocol)
        data_b = await wait_for_datagram(sink_b.protocol)
        assert data_a == payload
        assert data_b == payload

        await relay.stop()
        sink_a.transport.close()
        sink_b.transport.close()

    asyncio.run(_run())


def test_udp_source_port_binding():
    module = _load_module()

    async def _run():
        sink = await start_udp_sink()
        listen_port = reserve_udp_port()
        source_port = reserve_udp_port()
        relay = module.UdpRelay(
            hass=DummyHass(),
            listen_ip="127.0.0.1",
            listen_port=listen_port,
            listen_interface="",
            targets=[module.RelayTarget("127.0.0.1", sink.port)],
            bind_ip="",
            bind_interface="",
            source_port=source_port,
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

        protocol = relay._protocol  # noqa: SLF001
        sock = protocol._send_socket  # noqa: SLF001
        assert sock is not None
        assert sock.getsockname()[1] == source_port

        payload = b"bind-port"
        await send_udp_packet(payload, "127.0.0.1", listen_port)
        data = await wait_for_datagram(sink.protocol)
        assert data == payload

        await relay.stop()
        sink.transport.close()

    asyncio.run(_run())
