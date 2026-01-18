import socket
import struct
import subprocess
import re

def get_broadcast_addresses():
    """Ermittelt alle Broadcast-Adressen via ifconfig (macOS)"""
    broadcasts = []
    try:
        output = subprocess.check_output(['ifconfig'], text=True)
        current_ip = None
        for line in output.split('\n'):
            # IP-Adresse finden
            ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', line)
            if ip_match:
                current_ip = ip_match.group(1)
            # Broadcast finden
            bc_match = re.search(r'broadcast (\d+\.\d+\.\d+\.\d+)', line)
            if bc_match and current_ip:
                broadcasts.append((current_ip, bc_match.group(1)))
                current_ip = None
    except Exception as e:
        print(f"Warnung: Konnte Interfaces nicht lesen: {e}")
    return broadcasts

def create_artpoll():
    """Erstellt ein korrektes ArtPoll Paket"""
    packet = bytearray()
    packet.extend(b'Art-Net\x00')      # ID
    packet.extend(struct.pack('<H', 0x2000))  # OpCode ArtPoll
    packet.extend(struct.pack('>H', 14))      # ProtVer (High Byte first!)
    packet.extend(struct.pack('B', 0x00))     # Flags
    packet.extend(struct.pack('B', 0x00))     # DiagPriority
    return bytes(packet)

def parse_artpoll_reply(data):
    """Parst ein ArtPollReply Paket"""
    if len(data) < 207:
        return None
    
    info = {}
    info['ip'] = f"{data[10]}.{data[11]}.{data[12]}.{data[13]}"
    info['port'] = struct.unpack('<H', data[14:16])[0]
    info['firmware'] = struct.unpack('>H', data[16:18])[0]
    info['short_name'] = data[26:44].decode('ascii', errors='ignore').rstrip('\x00')
    info['long_name'] = data[44:108].decode('ascii', errors='ignore').rstrip('\x00')
    info['mac'] = ':'.join(f'{b:02x}' for b in data[201:207])
    return info

def main():
    print("=" * 50)
    print("ArtNet Node Discovery")
    print("=" * 50)
    
    # Netzwerk-Interfaces anzeigen
    broadcasts = get_broadcast_addresses()
    print(f"\nGefundene Netzwerk-Interfaces:")
    for ip, bc in broadcasts:
        print(f"  {ip} -> Broadcast: {bc}")
    
    if not broadcasts:
        print("FEHLER: Keine Netzwerk-Interfaces gefunden!")
        return
    
    # Socket erstellen
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(3)
    sock.bind(('', 6454))
    
    # ArtPoll senden
    artpoll = create_artpoll()
    print(f"\nSende ArtPoll ({len(artpoll)} bytes)...")
    
    for ip, bc in broadcasts:
        print(f"  -> Broadcast an {bc}:6454")
        sock.sendto(artpoll, (bc, 6454))
    
    # Auch an globalen Broadcast
    sock.sendto(artpoll, ('255.255.255.255', 6454))
    print(f"  -> Broadcast an 255.255.255.255:6454")
    
    # Auf Antworten warten
    print(f"\nWarte auf ArtPollReply (3 Sekunden Timeout)...")
    nodes_found = []
    
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            if data[:8] == b'Art-Net\x00':
                opcode = struct.unpack('<H', data[8:10])[0]
                if opcode == 0x2100:  # ArtPollReply
                    info = parse_artpoll_reply(data)
                    if info and addr[0] not in [n['source_ip'] for n in nodes_found]:
                        info['source_ip'] = addr[0]
                        nodes_found.append(info)
                        print(f"\n✓ Node gefunden: {addr[0]}")
                        print(f"    Short Name: {info['short_name']}")
                        print(f"    Long Name:  {info['long_name']}")
                        print(f"    MAC:        {info['mac']}")
                        print(f"    Firmware:   {info['firmware']}")
        except socket.timeout:
            break
    
    sock.close()
    
    # Zusammenfassung
    print("\n" + "=" * 50)
    if nodes_found:
        print(f"Gefunden: {len(nodes_found)} ArtNet Node(s)")
        for node in nodes_found:
            print(f"  - {node['source_ip']}: {node['short_name']}")
    else:
        print("Keine ArtNet Nodes gefunden.")
        print("\nMögliche Ursachen:")
        print("  - Keine ArtNet-Geräte im Netzwerk")
        print("  - Firewall blockiert UDP Port 6454")
        print("  - Geräte in anderem Subnetz")
    print("=" * 50)

if __name__ == "__main__":
    main()