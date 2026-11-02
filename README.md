# ArtNet Relay (Home Assistant)

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://www.hacs.xyz/docs/faq/custom_repositories/)
[![Release](https://img.shields.io/github/v/release/speedy3wk/ha-artnet-relay.svg)](https://github.com/speedy3wk/ha-artnet-relay/releases)

[![Add repository to Home Assistant](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=speedy3wk&repository=ha-artnet-relay&category=integration)

Relay Art-Net (UDP) packets from a listen socket to one or more broadcast/unicast targets. Designed for setups where Art-Net devices live on a different IP range (e.g., 2.x/10.x) and need a virtual/bind address on the HA host.

## Features
- Protocols: Art-Net, sACN, UDP, TCP.
- Listens on a configurable IP/port (optional interface binding).
- Relays to one or more targets.
- Optional bind IP on a selected interface (required by some Art-Net hardware).
- Config Flow + Options Flow UI.

## Installation (HACS)
1. Click the button above to add this repository as a custom repository in HACS (Integration).
2. Install **ArtNet Relay**.
3. Restart Home Assistant.
4. Add integration via **Settings → Devices & Services**.

## Configuration
All options are configured via the UI. Targets are entered as a list:

```
2.255.255.255:6454, 10.0.0.255:6454
```
or one per line.

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

## AI Notes
- Created using AI Tools.
- Generated Code is always validated/checked. 
- Not all features are validated against "real ArtNet hardware" yet. 