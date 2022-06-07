import socket
import json
from boltons.socketutils import BufferedSocket
from ncaa_live_stats import NCAALiveStats
from pprint import pprint


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
stats = NCAALiveStats()

params = {
    "type": "parameters",
    "types": "se,ac,mi,te,sc,box,pbp",
    "playbyplayOnConnect": 1,
}

sock.connect(("10.211.55.4", 7677))
sock.sendall(json.dumps(params).encode("utf-8"))
bsock = BufferedSocket(sock, maxsize=2097152, timeout=None)

while True:
    data = bsock.recv_until(b"\r\n")
    payload = json.loads(data)
    stats.receive(payload)
    num_actions = len(stats._game.actions)
    print(num_actions)
    if num_actions > 0:
        print(stats._game.actions[-1])
    if stats.is_ready:
        pprint(stats._game.home_team.players[1].__dict__)
