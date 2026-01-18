import asyncio
import importlib

from .relay_harness import reserve_tcp_port


def _load_module():
    return importlib.import_module("ha_artnet_relay")


def test_tcp_forwarding_to_targets():
    module = _load_module()

    async def _run():
        target_port = reserve_tcp_port()
        listen_port = reserve_tcp_port()
        received = asyncio.Queue()

        async def _handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
            data = await reader.read(1024)
            await received.put(data)
            writer.close()
            await writer.wait_closed()

        server = await asyncio.start_server(_handle, "127.0.0.1", target_port)

        relay = module.TcpRelay(
            listen_ip="127.0.0.1",
            listen_port=listen_port,
            targets=[module.RelayTarget("127.0.0.1", target_port)],
            protocol=module.PROTOCOL_TCP,
            allow_sources=[],
            deny_sources=[],
            artnet_universe=[],
            artnet_subnet=[],
            artnet_net=[],
            artnet_opcodes=[],
            rate_limit_pps=0,
        )
        assert await relay.start() is True

        reader, writer = await asyncio.open_connection("127.0.0.1", listen_port)
        payload = b"tcp-payload"
        writer.write(payload)
        await writer.drain()
        writer.close()
        await writer.wait_closed()

        data = await asyncio.wait_for(received.get(), timeout=1.0)
        assert data == payload

        await relay.stop()
        server.close()
        await server.wait_closed()

    asyncio.run(_run())
