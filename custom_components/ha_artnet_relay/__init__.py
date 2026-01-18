"""The ArtNet Relay integration."""
from __future__ import annotations

import asyncio
import logging
import socket
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .coordinator import ArtNetRelayCoordinator
from .const import (
    ARTNET_HEADER,
    CONF_AUTO_ADD_BIND_IP,
    CONF_ALLOW_SOURCES,
    CONF_ARTNET_NET,
    CONF_ARTNET_OPCODES,
    CONF_ARTNET_SUBNET,
    CONF_ARTNET_UNIVERSE,
    CONF_BIND_NETMASK,
    CONF_BROADCAST_BIND_IP,
    CONF_BROADCAST_IP,
    CONF_BROADCAST_PORT,
    CONF_DENY_SOURCES,
    CONF_LISTEN_INTERFACE,
    CONF_LISTEN_IP,
    CONF_LISTEN_PORT,
    CONF_NETWORK_INTERFACE,
    CONF_PROTOCOL,
    CONF_RATE_LIMIT_PPS,
    CONF_SOURCE_PORT,
    CONF_TARGETS,
    DEFAULT_AUTO_ADD_BIND_IP,
    DEFAULT_ALLOW_SOURCES,
    DEFAULT_ARTNET_NET,
    DEFAULT_ARTNET_OPCODES,
    DEFAULT_ARTNET_SUBNET,
    DEFAULT_ARTNET_UNIVERSE,
    DEFAULT_BIND_NETMASK,
    DEFAULT_BROADCAST_BIND_IP,
    DEFAULT_BROADCAST_IP,
    DEFAULT_BROADCAST_PORT,
    DEFAULT_DENY_SOURCES,
    DEFAULT_LISTEN_INTERFACE,
    DEFAULT_LISTEN_IP,
    DEFAULT_LISTEN_PORT,
    DEFAULT_NETWORK_INTERFACE,
    DEFAULT_PROTOCOL,
    DEFAULT_RATE_LIMIT_PPS,
    DEFAULT_SOURCE_PORT,
    DOMAIN,
    PROTOCOL_ARTNET,
    PROTOCOL_SACN,
    PROTOCOL_TCP,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

MAX_BIND_RETRIES = 60
RETRY_DELAY_SECONDS = 5

ARTNET_OPCODE_MAP: dict[str, bytes] = {
    "artdmx": b"\x00\x50",
    "artpoll": b"\x00\x20",
    "artpollreply": b"\x00\x21",
    "artsync": b"\x00\x52",
}


async def _try_add_ip_address(ip: str, netmask: str, interface: str) -> bool:
    """Try to add an IP address to the network interface."""
    try:
        cmd = ["ip", "addr", "add", f"{ip}/{netmask}", "dev", interface]
        _LOGGER.info("Attempting to add IP %s/%s to %s", ip, netmask, interface)

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode == 0:
            _LOGGER.info("Successfully added IP %s to %s", ip, interface)
            return True
        if b"RTNETLINK answers: File exists" in stderr:
            _LOGGER.info("IP %s already exists on %s", ip, interface)
            return True

        _LOGGER.warning(
            "Failed to add IP %s to %s: %s (code %d)",
            ip,
            interface,
            stderr.decode(),
            proc.returncode,
        )
        return False
    except Exception as err:
        _LOGGER.debug("Could not add IP address: %s", err)
        return False


def _guess_netmask(bind_ip: str, override: int) -> str:
    if override and override > 0:
        return str(override)
    if bind_ip.startswith("2."):
        return "8"
    if bind_ip.startswith("10."):
        return "8"
    if bind_ip.startswith("192.168."):
        return "24"
    if bind_ip.startswith("172."):
        return "12"
    return "24"


def _is_artnet(data: bytes) -> bool:
    return len(data) >= 8 and data[:8] == ARTNET_HEADER


def _is_sacn(data: bytes) -> bool:
    if len(data) < 16:
        return False
    if data[0:2] != b"\x00\x10":
        return False
    return data[4:16] == b"ASC-E1.17\x00\x00\x00"


def _get_filter(protocol: str) -> Callable[[bytes], bool]:
    if protocol == PROTOCOL_ARTNET:
        return _is_artnet
    if protocol == PROTOCOL_SACN:
        return _is_sacn
    return lambda data: True


def _get_artnet_opcode(data: bytes) -> bytes | None:
    if len(data) < 10:
        return None
    return data[8:10]


class RateLimiter:
    """Simple packet-per-second limiter."""

    def __init__(self, max_pps: int) -> None:
        self.max_pps = max_pps
        self._window_start = asyncio.get_running_loop().time()
        self._count = 0

    def allow(self) -> bool:
        if self.max_pps <= 0:
            return True
        now = asyncio.get_running_loop().time()
        if now - self._window_start >= 1.0:
            self._window_start = now
            self._count = 0
        if self._count >= self.max_pps:
            return False
        self._count += 1
        return True


@dataclass
class RelayTarget:
    """Relay target definition."""

    host: str
    port: int


def _parse_targets(value: object, default_port: int) -> list[RelayTarget]:
    targets: list[RelayTarget] = []
    if isinstance(value, list):
        for item in value:
            if not isinstance(item, dict):
                continue
            host = str(item.get("host", "")).strip()
            port = int(item.get("port", default_port))
            if host:
                targets.append(RelayTarget(host, port))
    return targets


def _parse_ip_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        parts = [p.strip() for p in value.replace("\n", ",").split(",")]
        return [p for p in parts if p]
    return []


def _parse_str_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _parse_int_list(value: object) -> list[int]:
    if isinstance(value, list):
        items: list[int] = []
        for item in value:
            try:
                items.append(int(item))
            except (TypeError, ValueError):
                continue
        return items
    if isinstance(value, str):
        items: list[int] = []
        parts = [p.strip() for p in value.replace("\n", ",").split(",")]
        for part in parts:
            if not part:
                continue
            try:
                items.append(int(part))
            except ValueError:
                continue
        return items
    return []


def _extract_artnet_fields(data: bytes) -> tuple[int, int, int] | None:
    if len(data) < 18:
        return None
    if not _is_artnet(data):
        return None
    if data[8:10] != b"\x00\x50":
        return None
    subuni = data[14]
    net = data[15]
    subnet = (subuni >> 4) & 0x0F
    universe = subuni & 0x0F
    return (net, subnet, universe)


class UdpRelayProtocol(asyncio.DatagramProtocol):
    """Asyncio Protocol for UDP relay."""

    def __init__(
        self,
        targets: list[RelayTarget],
        bind_ip: str,
        bind_interface: str,
        source_port: int,
        protocol: str,
        allow_sources: list[str],
        deny_sources: list[str],
        artnet_universe: list[int],
        artnet_subnet: list[int],
        artnet_net: list[int],
        artnet_opcodes: list[str],
        rate_limit_pps: int,
        hass: HomeAssistant,
        auto_add_bind_ip: bool,
        bind_netmask: int,
    ) -> None:
        self.targets = targets
        self.bind_ip = bind_ip
        self.bind_interface = bind_interface
        self.source_port = source_port
        self.protocol = protocol
        self.allow_sources = allow_sources
        self.deny_sources = deny_sources
        self.artnet_universe = artnet_universe
        self.artnet_subnet = artnet_subnet
        self.artnet_net = artnet_net
        self.artnet_opcodes = {
            ARTNET_OPCODE_MAP[opcode]
            for opcode in artnet_opcodes
            if opcode in ARTNET_OPCODE_MAP
        }
        self.rate_limiter = RateLimiter(rate_limit_pps)
        self.hass = hass
        self.auto_add_bind_ip = auto_add_bind_ip
        self.bind_netmask = bind_netmask
        self.transport: asyncio.DatagramTransport | None = None
        self._send_socket: socket.socket | None = None
        self._packet_count = 0
        self._socket_ready = False
        self._accept = _get_filter(protocol)
        self._last_packet: datetime | None = None
        self._error_count = 0

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        self.transport = transport
        _LOGGER.info("Relay listening socket ready")
        self.hass.async_create_task(self._setup_send_socket_with_retry())

    async def _setup_send_socket_with_retry(self) -> None:
        if self.auto_add_bind_ip and self.bind_ip and self.bind_interface:
            netmask = _guess_netmask(self.bind_ip, self.bind_netmask)
            await _try_add_ip_address(self.bind_ip, netmask, self.bind_interface)
            await asyncio.sleep(2)

        for attempt in range(MAX_BIND_RETRIES):
            try:
                self._setup_send_socket()
                if self._socket_ready:
                    return
            except Exception as err:
                _LOGGER.debug("Socket setup attempt %d failed: %s", attempt + 1, err)

            if attempt < MAX_BIND_RETRIES - 1:
                _LOGGER.info(
                    "Waiting for bind interface %s (attempt %d/%d)...",
                    self.bind_ip,
                    attempt + 1,
                    MAX_BIND_RETRIES,
                )
                await asyncio.sleep(RETRY_DELAY_SECONDS)

        _LOGGER.error(
            "Could not bind send socket after %d attempts. Relay will not work!",
            MAX_BIND_RETRIES,
        )

    def _setup_send_socket(self) -> None:
        if self._send_socket:
            try:
                self._send_socket.close()
            except Exception:
                pass
            self._send_socket = None
            self._socket_ready = False

        self._send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self._send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except (AttributeError, OSError):
            pass

        if self.bind_interface and hasattr(socket, "SO_BINDTODEVICE"):
            try:
                self._send_socket.setsockopt(
                    socket.SOL_SOCKET, socket.SO_BINDTODEVICE, self.bind_interface.encode()
                )
            except OSError as err:
                _LOGGER.warning("Failed to bind send socket to %s: %s", self.bind_interface, err)

        if self.bind_ip:
            self._send_socket.bind((self.bind_ip, self.source_port))
        elif self.source_port:
            self._send_socket.bind(("0.0.0.0", self.source_port))

        self._socket_ready = True

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        if not self._socket_ready or not self._send_socket:
            return
        source_ip = addr[0]
        if self.allow_sources and source_ip not in self.allow_sources:
            return
        if self.deny_sources and source_ip in self.deny_sources:
            return
        if not self._accept(data):
            return
        if self.protocol == PROTOCOL_ARTNET:
            opcode = _get_artnet_opcode(data)
            if opcode is None or (self.artnet_opcodes and opcode not in self.artnet_opcodes):
                return
            fields = _extract_artnet_fields(data)
            if opcode == ARTNET_OPCODE_MAP.get("artdmx"):
                if fields is None:
                    return
                net, subnet, universe = fields
                if self.artnet_net and net not in self.artnet_net:
                    return
                if self.artnet_subnet and subnet not in self.artnet_subnet:
                    return
                if self.artnet_universe and universe not in self.artnet_universe:
                    return
        if not self.rate_limiter.allow():
            return

        for target in self.targets:
            try:
                self._send_socket.sendto(data, (target.host, target.port))
                self._packet_count += 1
                self._last_packet = dt_util.utcnow()
            except OSError as err:
                _LOGGER.error("Failed to relay packet to %s:%d: %s", target.host, target.port, err)
                self._error_count += 1
                self._socket_ready = False
                self.hass.async_create_task(self._setup_send_socket_with_retry())
                break

        if self._packet_count <= 3 or self._packet_count % 100 == 0:
            _LOGGER.debug(
                "Relayed %d packets (%d bytes from %s)",
                self._packet_count,
                len(data),
                addr[0],
            )

    def error_received(self, exc: Exception) -> None:
        _LOGGER.error("Relay error: %s", exc)
        self._error_count += 1

    def connection_lost(self, exc: Exception | None) -> None:
        if self._send_socket:
            try:
                self._send_socket.close()
            except Exception:
                pass
            self._send_socket = None
        self._socket_ready = False
        _LOGGER.info("Relay stopped. Relayed %d packets total.", self._packet_count)

    @property
    def packet_count(self) -> int:
        return self._packet_count

    @property
    def last_packet(self) -> datetime | None:
        return self._last_packet

    @property
    def error_count(self) -> int:
        return self._error_count


class UdpRelay:
    """UDP relay implementation."""

    def __init__(
        self,
        hass: HomeAssistant,
        listen_ip: str,
        listen_port: int,
        listen_interface: str,
        targets: list[RelayTarget],
        bind_ip: str,
        bind_interface: str,
        source_port: int,
        protocol: str,
        allow_sources: list[str],
        deny_sources: list[str],
        artnet_universe: list[int],
        artnet_subnet: list[int],
        artnet_net: list[int],
        artnet_opcodes: list[str],
        rate_limit_pps: int,
        auto_add_bind_ip: bool,
        bind_netmask: int,
    ) -> None:
        self.hass = hass
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.listen_interface = listen_interface
        self.targets = targets
        self.bind_ip = bind_ip
        self.bind_interface = bind_interface
        self.source_port = source_port
        self.protocol = protocol
        self.allow_sources = allow_sources
        self.deny_sources = deny_sources
        self.artnet_universe = artnet_universe
        self.artnet_subnet = artnet_subnet
        self.artnet_net = artnet_net
        self.artnet_opcodes = artnet_opcodes
        self.rate_limit_pps = rate_limit_pps
        self.auto_add_bind_ip = auto_add_bind_ip
        self.bind_netmask = bind_netmask
        self._transport: asyncio.DatagramTransport | None = None
        self._protocol: UdpRelayProtocol | None = None

    async def start(self) -> bool:
        try:
            loop = asyncio.get_running_loop()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except (AttributeError, OSError):
                pass

            if self.listen_interface and hasattr(socket, "SO_BINDTODEVICE"):
                try:
                    sock.setsockopt(
                        socket.SOL_SOCKET, socket.SO_BINDTODEVICE, self.listen_interface.encode()
                    )
                except OSError as err:
                    _LOGGER.warning("Failed to bind listen socket to %s: %s", self.listen_interface, err)

            sock.bind((self.listen_ip, self.listen_port))

            self._transport, self._protocol = await loop.create_datagram_endpoint(
                lambda: UdpRelayProtocol(
                    self.targets,
                    self.bind_ip,
                    self.bind_interface,
                    self.source_port,
                    self.protocol,
                    self.allow_sources,
                    self.deny_sources,
                    self.artnet_universe,
                    self.artnet_subnet,
                    self.artnet_net,
                    self.artnet_opcodes,
                    self.rate_limit_pps,
                    self.hass,
                    self.auto_add_bind_ip,
                    self.bind_netmask,
                ),
                sock=sock,
            )

            _LOGGER.info(
                "Relay started (UDP %s): listening on %s:%d",
                self.protocol,
                self.listen_ip,
                self.listen_port,
            )
            return True
        except OSError as err:
            _LOGGER.error("Failed to start UDP relay: %s", err)
            return False

    async def stop(self) -> None:
        if self._transport:
            self._transport.close()
            self._transport = None
        packet_count = self._protocol.packet_count if self._protocol else 0
        _LOGGER.info("Relay stopped. Relayed %d packets.", packet_count)

    @property
    def stats(self) -> dict[str, object]:
        protocol = self._protocol
        return {
            "packet_count": protocol.packet_count if protocol else 0,
            "error_count": protocol.error_count if protocol else 0,
            "last_packet": protocol.last_packet if protocol else None,
            "targets": len(self.targets),
        }


class TcpRelay:
    """TCP relay implementation (send-only to targets)."""

    def __init__(
        self,
        listen_ip: str,
        listen_port: int,
        targets: list[RelayTarget],
        protocol: str,
        allow_sources: list[str],
        deny_sources: list[str],
        artnet_universe: list[int],
        artnet_subnet: list[int],
        artnet_net: list[int],
        artnet_opcodes: list[str],
        rate_limit_pps: int,
    ) -> None:
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.targets = targets
        self.protocol = protocol
        self.allow_sources = allow_sources
        self.deny_sources = deny_sources
        self.artnet_universe = artnet_universe
        self.artnet_subnet = artnet_subnet
        self.artnet_net = artnet_net
        self.artnet_opcodes = {
            ARTNET_OPCODE_MAP[opcode]
            for opcode in artnet_opcodes
            if opcode in ARTNET_OPCODE_MAP
        }
        self.rate_limiter = RateLimiter(rate_limit_pps)
        self._server: asyncio.base_events.Server | None = None
        self._target_writers: dict[str, asyncio.StreamWriter] = {}
        self._send_lock = asyncio.Lock()
        self._packet_count = 0
        self._error_count = 0
        self._last_packet: datetime | None = None
        self._accept = _get_filter(protocol)

    async def start(self) -> bool:
        try:
            self._server = await asyncio.start_server(
                self._handle_client, self.listen_ip, self.listen_port
            )
            _LOGGER.info(
                "Relay started (TCP %s): listening on %s:%d",
                self.protocol,
                self.listen_ip,
                self.listen_port,
            )
            return True
        except OSError as err:
            _LOGGER.error("Failed to start TCP relay: %s", err)
            return False

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

        for writer in self._target_writers.values():
            writer.close()
        self._target_writers.clear()
        _LOGGER.info("Relay stopped. Relayed %d packets.", self._packet_count)

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            peer = writer.get_extra_info("peername")
            if isinstance(peer, tuple) and peer:
                source_ip = peer[0]
                if self.allow_sources and source_ip not in self.allow_sources:
                    return
                if self.deny_sources and source_ip in self.deny_sources:
                    return
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                if not self._accept(data):
                    continue
                if self.protocol == PROTOCOL_ARTNET:
                    opcode = _get_artnet_opcode(data)
                    if opcode is None or (self.artnet_opcodes and opcode not in self.artnet_opcodes):
                        continue
                    fields = _extract_artnet_fields(data)
                    if opcode == ARTNET_OPCODE_MAP.get("artdmx"):
                        if fields is None:
                            continue
                        net, subnet, universe = fields
                        if self.artnet_net and net not in self.artnet_net:
                            continue
                        if self.artnet_subnet and subnet not in self.artnet_subnet:
                            continue
                        if self.artnet_universe and universe not in self.artnet_universe:
                            continue
                if not self.rate_limiter.allow():
                    continue
                await self._send_to_targets(data)
        finally:
            writer.close()
            await writer.wait_closed()

    async def _send_to_targets(self, data: bytes) -> None:
        async with self._send_lock:
            for target in self.targets:
                key = f"{target.host}:{target.port}"
                writer = self._target_writers.get(key)
                if writer is None or writer.is_closing():
                    try:
                        _, writer = await asyncio.open_connection(
                            target.host, target.port
                        )
                        self._target_writers[key] = writer
                    except OSError as err:
                        _LOGGER.error(
                            "Failed to connect to %s:%d: %s",
                            target.host,
                            target.port,
                            err,
                        )
                        self._error_count += 1
                        continue

                try:
                    writer.write(data)
                    await writer.drain()
                    self._packet_count += 1
                    self._last_packet = dt_util.utcnow()
                except OSError as err:
                    _LOGGER.error(
                        "Failed to relay TCP packet to %s:%d: %s",
                        target.host,
                        target.port,
                        err,
                    )
                    self._error_count += 1
                    writer.close()
                    self._target_writers.pop(key, None)

    @property
    def stats(self) -> dict[str, object]:
        return {
            "packet_count": self._packet_count,
            "error_count": self._error_count,
            "last_packet": self._last_packet,
            "targets": len(self.targets),
        }


def _get_value(entry: ConfigEntry, key: str, default: Any) -> Any:
    if key in entry.options:
        return entry.options[key]
    if key in entry.data:
        return entry.data[key]
    return default


def _as_str(value: Any, default: str) -> str:
    if value is None:
        return default
    return str(value)


def _as_int(value: Any, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    return bool(value)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ArtNet Relay from a config entry."""
    listen_ip = _as_str(_get_value(entry, CONF_LISTEN_IP, DEFAULT_LISTEN_IP), DEFAULT_LISTEN_IP)
    listen_port = _as_int(_get_value(entry, CONF_LISTEN_PORT, DEFAULT_LISTEN_PORT), DEFAULT_LISTEN_PORT)
    listen_interface = _as_str(
        _get_value(entry, CONF_LISTEN_INTERFACE, DEFAULT_LISTEN_INTERFACE),
        DEFAULT_LISTEN_INTERFACE,
    )
    broadcast_ip = _as_str(
        _get_value(entry, CONF_BROADCAST_IP, DEFAULT_BROADCAST_IP), DEFAULT_BROADCAST_IP
    )
    broadcast_port = _as_int(
        _get_value(entry, CONF_BROADCAST_PORT, DEFAULT_BROADCAST_PORT),
        DEFAULT_BROADCAST_PORT,
    )
    bind_ip = _as_str(
        _get_value(entry, CONF_BROADCAST_BIND_IP, DEFAULT_BROADCAST_BIND_IP),
        DEFAULT_BROADCAST_BIND_IP,
    )
    bind_interface = _as_str(
        _get_value(entry, CONF_NETWORK_INTERFACE, DEFAULT_NETWORK_INTERFACE),
        DEFAULT_NETWORK_INTERFACE,
    )
    protocol = _as_str(_get_value(entry, CONF_PROTOCOL, DEFAULT_PROTOCOL), DEFAULT_PROTOCOL)
    auto_add_bind_ip = _as_bool(
        _get_value(entry, CONF_AUTO_ADD_BIND_IP, DEFAULT_AUTO_ADD_BIND_IP),
        DEFAULT_AUTO_ADD_BIND_IP,
    )
    bind_netmask = _as_int(
        _get_value(entry, CONF_BIND_NETMASK, DEFAULT_BIND_NETMASK),
        DEFAULT_BIND_NETMASK,
    )
    source_port = _as_int(
        _get_value(entry, CONF_SOURCE_PORT, DEFAULT_SOURCE_PORT),
        DEFAULT_SOURCE_PORT,
    )
    allow_sources = _parse_ip_list(
        _get_value(entry, CONF_ALLOW_SOURCES, DEFAULT_ALLOW_SOURCES)
    )
    deny_sources = _parse_ip_list(
        _get_value(entry, CONF_DENY_SOURCES, DEFAULT_DENY_SOURCES)
    )
    artnet_universe = _parse_int_list(
        _get_value(entry, CONF_ARTNET_UNIVERSE, DEFAULT_ARTNET_UNIVERSE)
    )
    artnet_subnet = _parse_int_list(
        _get_value(entry, CONF_ARTNET_SUBNET, DEFAULT_ARTNET_SUBNET)
    )
    artnet_net = _parse_int_list(
        _get_value(entry, CONF_ARTNET_NET, DEFAULT_ARTNET_NET)
    )
    artnet_opcodes = _parse_str_list(
        _get_value(entry, CONF_ARTNET_OPCODES, DEFAULT_ARTNET_OPCODES)
    )
    rate_limit_pps = _as_int(
        _get_value(entry, CONF_RATE_LIMIT_PPS, DEFAULT_RATE_LIMIT_PPS),
        DEFAULT_RATE_LIMIT_PPS,
    )

    targets_value = _get_value(entry, CONF_TARGETS, None)
    targets = _parse_targets(targets_value, broadcast_port)
    if not targets:
        targets = [RelayTarget(broadcast_ip, broadcast_port)]

    if protocol == PROTOCOL_TCP:
        relay: UdpRelay | TcpRelay = TcpRelay(
            listen_ip=listen_ip,
            listen_port=listen_port,
            targets=targets,
            protocol=protocol,
            allow_sources=allow_sources,
            deny_sources=deny_sources,
            artnet_universe=artnet_universe,
            artnet_subnet=artnet_subnet,
            artnet_net=artnet_net,
            artnet_opcodes=artnet_opcodes,
            rate_limit_pps=rate_limit_pps,
        )
    else:
        relay = UdpRelay(
            hass=hass,
            listen_ip=listen_ip,
            listen_port=listen_port,
            listen_interface=listen_interface,
            targets=targets,
            bind_ip=bind_ip,
            bind_interface=bind_interface,
            source_port=source_port,
            protocol=protocol,
            allow_sources=allow_sources,
            deny_sources=deny_sources,
            artnet_universe=artnet_universe,
            artnet_subnet=artnet_subnet,
            artnet_net=artnet_net,
            artnet_opcodes=artnet_opcodes,
            rate_limit_pps=rate_limit_pps,
            auto_add_bind_ip=auto_add_bind_ip,
            bind_netmask=bind_netmask,
        )

    if not await relay.start():
        return False

    hass.data.setdefault(DOMAIN, {})
    coordinator = ArtNetRelayCoordinator(hass, relay)
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = {
        "relay": relay,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    data = hass.data[DOMAIN].pop(entry.entry_id)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    await data["relay"].stop()
    return unload_ok
