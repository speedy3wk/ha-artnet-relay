# ArtNet Relay (Home Assistant)

[![Marketplace custom repository](https://img.shields.io/badge/Marketplace-Custom-orange.svg)](https://www.home-assistant.io/integrations/marketplace/#custom-repositories)
[![Release](https://img.shields.io/github/v/release/speedy3wk/ha-artnet-relay.svg)](https://github.com/speedy3wk/ha-artnet-relay/releases)

Relay Art-Net (UDP) packets from a listen socket to one or more broadcast/unicast targets. Designed for setups where Art-Net devices live on a different IP range (e.g., 2.x/10.x) and need a virtual/bind address on the HA host.

## Features
- Protocols: Art-Net, sACN, UDP, TCP.
- Listens on a configurable IP/port (optional interface binding).
- Relays to one or more targets.
- Optional bind IP on a selected interface (required by some Art-Net hardware).
- Config Flow + Options Flow UI.

## Installation

### Marketplace (recommended, Home Assistant 2026.11+)

The [Marketplace](https://www.home-assistant.io/integrations/marketplace/) is built into Home Assistant 2026.11 and newer.

[![Open in Marketplace](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=speedy3wk&repository=ha-artnet-relay&category=integration)

1. Open **Settings → Marketplace** as an administrator and accept the community-content warning if prompted.
2. Select **Add from link**, enter `https://github.com/speedy3wk/ha-artnet-relay` and select **Add**. Connect GitHub if prompted. If asked for a content type, select **Integration**.
3. Open **ArtNet Relay** and select **Install**.
4. Follow the integration setup flow. If it does not open, add **ArtNet Relay** via **Settings → Devices & Services**. Restart only if the Marketplace requests it.

Integration updates still require a Home Assistant restart.

On older supported Home Assistant versions, add this repository to HACS as an **Integration**, install it and restart before adding the integration.
Existing HACS installations migrate automatically to the Marketplace when updating to Home Assistant 2026.11.

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