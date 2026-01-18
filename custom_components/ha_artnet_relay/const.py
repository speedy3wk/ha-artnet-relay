"""Constants for the ArtNet Relay integration."""

DOMAIN = "ha_artnet_relay"

# Config keys
CONF_LISTEN_IP = "listen_ip"
CONF_LISTEN_PORT = "listen_port"
CONF_BROADCAST_IP = "broadcast_ip"
CONF_BROADCAST_PORT = "broadcast_port"
CONF_BROADCAST_BIND_IP = "broadcast_bind_ip"
CONF_NETWORK_INTERFACE = "network_interface"
CONF_LISTEN_INTERFACE = "listen_interface"
CONF_PROTOCOL = "protocol"
CONF_TARGETS = "targets"
CONF_AUTO_ADD_BIND_IP = "auto_add_bind_ip"
CONF_BIND_NETMASK = "bind_netmask"
CONF_SOURCE_PORT = "source_port"
CONF_ALLOW_SOURCES = "allow_sources"
CONF_DENY_SOURCES = "deny_sources"
CONF_ARTNET_UNIVERSE = "artnet_universe"
CONF_ARTNET_SUBNET = "artnet_subnet"
CONF_ARTNET_NET = "artnet_net"
CONF_ARTNET_OPCODES = "artnet_opcodes"
CONF_RATE_LIMIT_PPS = "rate_limit_pps"

# Defaults
DEFAULT_LISTEN_IP = "0.0.0.0"
DEFAULT_LISTEN_PORT = 6455
DEFAULT_BROADCAST_IP = "2.255.255.255"
DEFAULT_BROADCAST_PORT = 6454
DEFAULT_BROADCAST_BIND_IP = "2.0.1.1"
DEFAULT_NETWORK_INTERFACE = ""
DEFAULT_LISTEN_INTERFACE = ""
DEFAULT_PROTOCOL = "artnet"
DEFAULT_AUTO_ADD_BIND_IP = False
DEFAULT_BIND_NETMASK = 0
DEFAULT_SOURCE_PORT = 6454
DEFAULT_ALLOW_SOURCES: list[str] = []
DEFAULT_DENY_SOURCES: list[str] = []
DEFAULT_ARTNET_UNIVERSE: list[int] = []
DEFAULT_ARTNET_SUBNET: list[int] = []
DEFAULT_ARTNET_NET: list[int] = []
DEFAULT_ARTNET_OPCODES: list[str] = ["artdmx"]
DEFAULT_RATE_LIMIT_PPS = 0

ARTNET_OPCODES = ["artdmx", "artpoll", "artpollreply", "artsync"]

PROTOCOL_ARTNET = "artnet"
PROTOCOL_SACN = "sacn"
PROTOCOL_UDP = "udp"
PROTOCOL_TCP = "tcp"
PROTOCOLS = [PROTOCOL_ARTNET, PROTOCOL_SACN, PROTOCOL_UDP, PROTOCOL_TCP]

# ArtNet
ARTNET_HEADER = b"Art-Net\x00"
