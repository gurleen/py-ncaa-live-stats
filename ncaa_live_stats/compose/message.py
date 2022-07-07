from typing import Callable, Optional

import inflection
from loguru import logger
from ..structs import Action, ActionType, Game, Player


# CONSTANTS

EXPANSIONS = {
    "tipin": "tip in",
    "alleyoop": "alley oop",
    "drivinglayup": "driving layup",
    "hookshot": "hook shot",
    "floatingjumpshot": "floating jumpshot",
    "stepbackjumpshot": "stepback jumpshot",
    "pullupjumpshot": "pull up jumpshot",
    "turnaroundjumpshot": "turn around jumpshot",
    "wrongbasket": "wrong basket",
    "1freethrow": "one free throw",
    "2freethrow": "two free throws",
    "3freethrow": "three free throws",
    "oneandone": "one and one",
    "flagrant1": "flagrant 1",
    "flagrant2": "flagrant 2",
    "looseball": "loose ball",
    "classa": "class A",
    "classb": "class B",
    "benchclassb": "bench class B",
    "coachclassb": "coach class B",
    "coachindirect": "coach indirect",
    "contactdeadball": "dead ball contact"
}

ACTION_LITERALS = {
    ActionType.TWOPT: "two point",
    ActionType.THREEPT: "three point",
    ActionType.FREETHROW: "free throw"
}

class term:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# HELPER FUNCTIONS

def capitalize(s: str) -> str:
    """Capitalize first letter of a string.

    Args:
        s (str): Input

    Returns:
        str: Output, capitalized
    """
    return s[0].upper() + s[1:]


def expand(s: str) -> str:
    """Get expansion for given string, else return itself.

    Args:
        s (str): _description_

    Returns:
        str: _description_
    """
    return EXPANSIONS.get(s, s)

# HANDLERS


def get_action_player(action: Action, game: Game) -> Optional[Player]:
    try:
        return game.get_team_by_number(action.team_number).players[action.player_number]
    except KeyError:
        return None

def get_action_code(action: Action, game: Game) -> str:
    return game.get_team_by_number(action.team_number).code

def get_player_string(action: Action, game: Game) -> str:
    player = get_action_player(action, game)
    return f"{term.UNDERLINE}{term.BOLD}{player.full_name} [{get_action_code(action, game)}]{term.ENDC}"

def compose_scoring_play(action: Action, game: Game) -> str:
    play_type = ACTION_LITERALS.get(action.action_type, "")
    full_sub_type = EXPANSIONS.get(action.sub_type, action.sub_type)
    player = get_player_string(action, game)
    if player:
        return f"{player} made a {play_type} {full_sub_type}."


def compose_free_throw(action: Action, game: Game) -> str:
    player = get_player_string(action, game)
    sub_type = action.sub_type
    current, given = sub_type[0], sub_type[-1]
    return f"{player} made free throw {current} of {given}."


def compose_simple_action(action: Action, game: Game, kind: str = "Action") -> str:
    player = get_player_string(action, game)
    return f"{kind} by {player}."


def compose_rebound(action: Action, game: Game) -> str:
    if action.player_number == 0:
        team = game.get_team_by_number(action.team_number)
        name = f"{term.BOLD}{team.name}{term.ENDC}"
    else:
        name = get_player_string(action, game)
    subtype = inflection.titleize(action.sub_type)
    return f"{subtype} rebound by {name}."


def compose_foulon(action: Action, game: Game) -> str:
    player = get_player_string(action, game)
    return f"Foul drawn by {player}."
    

def compose_foul(action: Action, game: Game) -> str:
    if action.player_number == 0 or action.player_number == None:
        team = game.get_team_by_number(action.team_number)
        if action.sub_type == "coachTechnical":
            name = team.name + " coach"
        elif action.sub_type == "benchTechnical":
            name = team.name + " bench"
        else:
            name = team.name
    else:
        name = get_player_string(action, game)
    response = f"{inflection.titleize(expand(action.sub_type))} foul on {term.BOLD}{name}{term.ENDC}."
    qualifiers = set(action.qualifiers.copy())
    for ft_kind in ["1freethrow", "2freethrow", "3freethrow", "oneandone"]:
        if ft_kind in qualifiers:
            qualifiers.remove(ft_kind)
            response += f" Shooting {expand(ft_kind)}."
            break
    
    if len(qualifiers) > 0:
        response += f" Foul classified as {expand(qualifiers.pop())}."

    return response


def compose_timeout(action: Action, game: Game) -> str:
    if action.team_number == 0:
        if action.sub_type == "commercial":
            return f"{term.BOLD}{term.FAIL}MEDIA TIMEOUT.{term.ENDC}"
        return "Timeout taken by the officials."
    else:
        team = game.get_team_by_number(action.team_number)
        duration = "60s" if action.sub_type == "full" else "30s"
        return f"{duration} timeout taken by {term.BOLD}{team.name}{term.ENDC}."


MESSAGES: dict[ActionType, Callable] = {
    ActionType.GAME: lambda a, _: f"Game has {a.sub_type}ed.",
    ActionType.PERIOD: lambda a, _: f"Period {a.period} has {a.sub_type}ed.",
    ActionType.TWOPT: compose_scoring_play,
    ActionType.THREEPT: compose_scoring_play,
    ActionType.FREETHROW: compose_free_throw,
    ActionType.ASSIST: lambda a, g: compose_simple_action(a, g, "Assist"),
    ActionType.BLOCK: lambda a, g: compose_simple_action(a, g, "Block"),
    ActionType.REBOUND: compose_rebound,
    ActionType.FOULON: compose_foulon,
    ActionType.FOUL: compose_foul,
    ActionType.TIMEOUT: compose_timeout
}


def compose_action_message(action: Action, game: Game) -> str:
    handler = MESSAGES.get(action.action_type)
    if handler:
        message = handler(action, game)
        if message:
            return f"{term.HEADER}[{action.period_norm} {action.clock_norm} {action.action_number}]{term.ENDC} {message}"
    else:
        logger.error(f"UNHANDLED ACTION TYPE {action.action_type}")
        logger.error(action)
    return ""