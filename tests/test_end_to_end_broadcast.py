import asyncio
import importlib
import os
import re
import subprocess
import sys

import pytest

from .relay_harness import (
    DummyHass,
    reserve_udp_port,
    send_udp_packet,
    start_udp_sink_on_port,
    wait_for_datagram,
    wait_for_relay_socket,
)


def _load_module():
    return importlib.import_module("ha_artnet_relay")


def _detect_macos_broadcast() -> tuple[str, str, str] | None:
    if sys.platform != "darwin":
        return None
    try:
        route = subprocess.run(
            ["route", "-n", "get", "default"],
            check=True,
            capture_output=True,
            text=True,
        )
        iface_match = re.search(r"interface: (\S+)", route.stdout)
        if not iface_match:
            return None
        iface = iface_match.group(1)

        ifconfig = subprocess.run(
            ["ifconfig", iface],
            check=True,
            capture_output=True,
            text=True,
        )
        inet_match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", ifconfig.stdout)
        bcast_match = re.search(r"broadcast (\d+\.\d+\.\d+\.\d+)", ifconfig.stdout)
        if not inet_match or not bcast_match:
            return None
        bind_ip = inet_match.group(1)
        broadcast = bcast_match.group(1)
        return broadcast, bind_ip, "0.0.0.0"
    except (OSError, subprocess.CalledProcessError):
        return None


def test_udp_broadcast_target_forwarding():
    module = _load_module()

    broadcast_target = os.environ.get("ARTNET_TEST_BROADCAST_TARGET")
    bind_ip = os.environ.get("ARTNET_TEST_BIND_IP", "")
    listen_ip = os.environ.get("ARTNET_TEST_LISTEN_IP", "0.0.0.0")
    if not broadcast_target:
        detected = _detect_macos_broadcast()
        if detected:
            broadcast_target, bind_ip, listen_ip = detected
        else:
            pytest.skip("Set ARTNET_TEST_BROADCAST_TARGET or enable macOS auto-detect")

    async def _run():
        port = reserve_udp_port()
        sink = await start_udp_sink_on_port("0.0.0.0", port)
        listen_port = reserve_udp_port()
        relay = module.UdpRelay(
            hass=DummyHass(),
            listen_ip=listen_ip,
            listen_port=listen_port,
            listen_interface="",
            targets=[module.RelayTarget(broadcast_target, port)],
            bind_ip=bind_ip,
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

        payload = b"broadcast"
        await send_udp_packet(payload, "127.0.0.1", listen_port)
        data = await wait_for_datagram(sink.protocol)
        assert data == payload

        await relay.stop()
        sink.transport.close()

    asyncio.run(_run())
