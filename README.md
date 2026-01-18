# ArtNet Relay (Home Assistant)

Relay Art-Net (UDP) packets from a listen socket to one or more broadcast/unicast targets. Designed for setups where Art-Net devices live on a different IP range (e.g., 2.x/10.x) and need a virtual/bind address on the HA host.

## Features
- Protocols: Art-Net, sACN, UDP, TCP.
- Listens on a configurable IP/port (optional interface binding).
- Relays to one or more targets.
- Optional bind IP on a selected interface (required by some Art-Net hardware).
- Config Flow + Options Flow UI.

## Installation (HACS)
1. Add this repository as a custom repository (Integration).
2. Install **ArtNet Relay**.
3. Restart Home Assistant.
4. Add integration via **Settings → Devices & Services**.

## Configuration
All options are configured via the UI. Targets are a list of objects:

```json
[
	{"host": "2.255.255.255", "port": 6454},
	{"host": "10.0.0.255", "port": 6454}
]
```

Optional filters:
- Allow source IPs (list)
- Deny source IPs (list)
- ArtNet Universe/Subnet/Net filters (lists)

Advanced:
- ArtNet OpCodes filter (list of strings)
- Rate limit (packets per second)

## Notes
- Binding to port 6454 may require elevated privileges on some systems.
- Some devices only accept packets from source port 6454.

## Support
Open an issue on GitHub with logs and configuration details.
