from __future__ import annotations

import asyncio
import socket
from dataclasses import dataclass
from typing import Tuple

import importlib


def _load_module():
    return importlib.import_module("ha_artnet_relay")


@dataclass
class UdpSink:
    transport: asyncio.DatagramTransport
    protocol: "UdpSinkProtocol"
    port: int


class UdpSinkProtocol(asyncio.DatagramProtocol):
    def __init__(self) -> None:
        self.queue: asyncio.Queue[Tuple[bytes, Tuple[str, int]]] = asyncio.Queue()

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        self.queue.put_nowait((data, addr))


async def start_udp_sink(host: str = "127.0.0.1") -> UdpSink:
    loop = asyncio.get_running_loop()
    protocol = UdpSinkProtocol()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: protocol, local_addr=(host, 0)
    )
    port = transport.get_extra_info("sockname")[1]
    return UdpSink(transport=transport, protocol=protocol, port=port)


async def start_udp_sink_on_port(host: str, port: int) -> UdpSink:
    loop = asyncio.get_running_loop()
    protocol = UdpSinkProtocol()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except (AttributeError, OSError):
        pass
    sock.bind((host, port))
    transport, _ = await loop.create_datagram_endpoint(lambda: protocol, sock=sock)
    return UdpSink(transport=transport, protocol=protocol, port=port)


async def wait_for_datagram(protocol: UdpSinkProtocol, timeout: float = 1.0) -> bytes:
    data, _ = await asyncio.wait_for(protocol.queue.get(), timeout=timeout)
    return data


def reserve_udp_port(host: str = "127.0.0.1") -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def reserve_tcp_port(host: str = "127.0.0.1") -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


class DummyHass:
    def async_create_task(self, coro):
        return asyncio.create_task(coro)


async def wait_for_relay_socket(relay, timeout: float = 2.0) -> None:
    module = _load_module()
    if not isinstance(relay, module.UdpRelay):
        return
    end = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < end:
        protocol = relay._protocol  # noqa: SLF001
        if protocol and protocol._socket_ready:  # noqa: SLF001
            return
        await asyncio.sleep(0.01)
    raise AssertionError("Relay send socket not ready")


def make_artnet_packet(opcode: bytes, universe: int = 0, subnet: int = 0, net: int = 0) -> bytes:
    data = bytearray(18)
    data[0:8] = b"Art-Net\x00"
    data[8:10] = opcode
    data[14] = ((subnet & 0x0F) << 4) | (universe & 0x0F)
    data[15] = net & 0x7F
    return bytes(data)


def make_artnet_dmx_packet(universe: int = 0, subnet: int = 0, net: int = 0) -> bytes:
    return make_artnet_packet(b"\x00\x50", universe=universe, subnet=subnet, net=net)


def make_sacn_packet() -> bytes:
    data = bytearray(48)
    data[0:2] = b"\x00\x10"
    data[4:16] = b"ASC-E1.17\x00\x00\x00"
    data[16:] = b"\x00" * (48 - 16)
    return bytes(data)


async def send_udp_packet(data: bytes, host: str, port: int) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(data, (host, port))
    finally:
        sock.close()
