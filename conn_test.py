import socket
import json
from boltons.socketutils import BufferedSocket
from ncaa_live_stats import NCAALiveStats
from ncaa_live_stats.compose.player import compose_player_statline


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
stats = NCAALiveStats()

params = {
    "type": "parameters",
    "types": "se,ac,mi,te,sc,pbp",
    "playbyplayOnConnect": 1,
}

sock.connect(("10.37.129.4", 7677))
sock.sendall(json.dumps(params).encode("utf-8"))
bsock = BufferedSocket(sock, maxsize=2097152, timeout=None)

while True:
    data = bsock.recv_until(b"\r\n")
    payload = json.loads(data)
    stats.receive(payload)
