from typing import Union
from ..structs import Player


PCT_REPLACE = {
    "FG": "field_goals_fraction",
    "3FG": "three_points_fraction",
    "FT": "free_throws_fraction"
}


def compose_player_statline(player: Player) -> str:
    stats = player.stats
    line_stats = {
        "AST": stats.assists,
        "BLK": stats.blocks,
        "REB": stats.rebounds_total,
        "FG": stats.field_goals_percentage,
        "3FG": stats.three_pointers_percentage,
        "FT": stats.free_throws_percentage
    }

    zeros_removed = {k: v for k, v in line_stats.items() if not v == 0}
    sorted_stats = sorted(zeros_removed.keys(), key=zeros_removed.get, reverse=True)

    
    output = f"{stats.points} PTS"
    for stat in sorted_stats:
        if stat in PCT_REPLACE:
            value = getattr(stats, PCT_REPLACE[stat])
        else:
            value = line_stats.get(stat)
        output += f", {value} {stat}"
    
    return output.lstrip()