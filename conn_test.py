import sys
import socket
import json
from boltons.socketutils import BufferedSocket
from ncaa_live_stats import NCAALiveStats
from ncaa_live_stats.compose.player import compose_player_statline
from ncaa_live_stats.structs import ActionType, Game
from loguru import logger


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
stats = NCAALiveStats()

logger.remove()
logger.add(sys.stdout, level="INFO")


def track_scoring_drought(game: Game):
    last_action = game.actions[-1]
    if last_action.is_scoring_play:
        team = last_action.get_team(game)
        print(f"Team {team.name} last score time is {last_action.clock_norm}")
        if last_action.action_type != ActionType.FREETHROW:
            print(f"Team {team.name} last FG time is {last_action.clock_norm}")

def get_starters(game: Game):
    home_starters = [
        p.full_name for p in game.home_team.players.values() if p.is_starter
    ]
    logger.info(f"Home starters: {home_starters}")
    away_starters = [
        p.full_name for p in game.away_team.players.values() if p.is_starter
    ]
    logger.info(f"Away starters: {away_starters}")


stats.add_listener("action", track_scoring_drought)
stats.add_listener("teams", get_starters)

params = {
    "type": "parameters",
    "types": "se,ac,mi,te,sc,pbp,box",
    "playbyplayOnConnect": 1,
}

sock.connect(("10.211.55.4", 7677))
sock.sendall(json.dumps(params).encode("utf-8"))
bsock = BufferedSocket(sock, maxsize=2097152, timeout=None)

while True:
    data = bsock.recv_until(b"\r\n")
    payload = json.loads(data)
    stats.receive(payload)
