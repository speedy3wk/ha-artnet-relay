import asyncio
import importlib


def _load_module():
    return importlib.import_module("ha_artnet_relay")


class DummySocket:
    def __init__(self):
        self.sent = []

    def sendto(self, data, addr):
        self.sent.append((data, addr))


class DummyHass:
    def async_create_task(self, coro):
        return None


def _artnet_packet(opcode=b"\x00\x50", subuni=0x00, net=0x00):
    data = bytearray(18)
    data[0:8] = b"Art-Net\x00"
    data[8:10] = opcode
    data[14] = subuni
    data[15] = net
    return bytes(data)


def test_allow_deny_and_opcode_filters():
    module = _load_module()

    async def _run():
        protocol = module.UdpRelayProtocol(
            targets=[module.RelayTarget("2.255.255.255", 6454)],
            bind_ip="2.0.1.1",
            bind_interface="end0",
            source_port=6454,
            protocol=module.PROTOCOL_ARTNET,
            allow_sources=["1.1.1.1"],
            deny_sources=["2.2.2.2"],
            artnet_universe=[],
            artnet_subnet=[],
            artnet_net=[],
            artnet_opcodes=["artdmx"],
            rate_limit_pps=0,
            hass=DummyHass(),
            auto_add_bind_ip=False,
            bind_netmask=0,
        )
        protocol._send_socket = DummySocket()
        protocol._socket_ready = True

        # Source not allowed
        protocol.datagram_received(_artnet_packet(), ("9.9.9.9", 1234))
        assert protocol._send_socket.sent == []

        # Denied source
        protocol.datagram_received(_artnet_packet(), ("2.2.2.2", 1234))
        assert protocol._send_socket.sent == []

        # Allowed source but opcode mismatch
        protocol.datagram_received(
            _artnet_packet(opcode=module.ARTNET_OPCODE_MAP["artsync"]),
            ("1.1.1.1", 1234),
        )
        assert protocol._send_socket.sent == []

        # Allowed source and opcode match
        protocol.datagram_received(_artnet_packet(), ("1.1.1.1", 1234))
        assert len(protocol._send_socket.sent) == 1

    asyncio.run(_run())


def test_artnet_universe_filter():
    module = _load_module()

    async def _run():
        protocol = module.UdpRelayProtocol(
            targets=[module.RelayTarget("2.255.255.255", 6454)],
            bind_ip="2.0.1.1",
            bind_interface="end0",
            source_port=6454,
            protocol=module.PROTOCOL_ARTNET,
            allow_sources=[],
            deny_sources=[],
            artnet_universe=[1],
            artnet_subnet=[2],
            artnet_net=[3],
            artnet_opcodes=["artdmx"],
            rate_limit_pps=0,
            hass=DummyHass(),
            auto_add_bind_ip=False,
            bind_netmask=0,
        )
        protocol._send_socket = DummySocket()
        protocol._socket_ready = True

        # net=3, subnet=2, universe=1 (subuni upper 4 bits subnet, lower 4 bits universe)
        packet = _artnet_packet(subuni=(2 << 4) | 1, net=3)
        protocol.datagram_received(packet, ("1.1.1.1", 1234))
        assert len(protocol._send_socket.sent) == 1

        # Universe mismatch
        packet = _artnet_packet(subuni=(2 << 4) | 2, net=3)
        protocol.datagram_received(packet, ("1.1.1.1", 1234))
        assert len(protocol._send_socket.sent) == 1

    asyncio.run(_run())


def test_rate_limit_drops_packets():
    module = _load_module()

    async def _run():
        protocol = module.UdpRelayProtocol(
            targets=[module.RelayTarget("2.255.255.255", 6454)],
            bind_ip="2.0.1.1",
            bind_interface="end0",
            source_port=6454,
            protocol=module.PROTOCOL_ARTNET,
            allow_sources=[],
            deny_sources=[],
            artnet_universe=[],
            artnet_subnet=[],
            artnet_net=[],
            artnet_opcodes=["artdmx"],
            rate_limit_pps=1,
            hass=DummyHass(),
            auto_add_bind_ip=False,
            bind_netmask=0,
        )
        protocol._send_socket = DummySocket()
        protocol._socket_ready = True

        packet = _artnet_packet()
        protocol.datagram_received(packet, ("1.1.1.1", 1234))
        protocol.datagram_received(packet, ("1.1.1.1", 1234))
        assert len(protocol._send_socket.sent) == 1

    asyncio.run(_run())
