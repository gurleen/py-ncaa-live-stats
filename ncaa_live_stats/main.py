from collections import defaultdict
import traceback
from dataclasses import asdict
from datetime import datetime
from typing import Any, Callable, List, Literal, TypeVar, DefaultDict

import inflection
from dateutil.parser import parse as dt_parse
from loguru import logger

from . import structs
from ncaa_live_stats.compose.message import compose_action_message

T = TypeVar("T")


def nested_get(mapping: dict, value: str) -> Any:
    """Returns a deeply nested value from a dictionary
    based on a dot-separated value. If value is not found,
    will return None.

    ex. `foo.bar` from `{"foo": {"bar": "answer"}}`
    would return `"answer"`

    Args:
        mapping (dict): Mapping to search
        value (str): Dot-separated value to get

    Returns:
        Any: Requested value or None
    """
    key_list = value.split(".")
    x = mapping
    try:
        for key in key_list:
            x = x[key]
        return x
    except KeyError:
        return None


def extract(message: dict, key: str, cast_to: T = str) -> T:
    """Get arbitrarly-nested value from `message` using
    dot-separated `key` and convert it to type `cast_to`

    Args:
        message (dict): Mapping to extract from
        key (str): Dot-separated key of requested value
        cast_to (T, optional): Type to convert value to. Defaults to str.

    Returns:
        T: Requested value
    """
    value = nested_get(message, key)
    if value == None or cast_to == str:
        return value
    try:
        return cast_to(value)
    except ValueError:
        return cast_to()


class NCAALiveStats:
    """Parser and datastore for messages from 
    Genius Sports' NCAA Live Stats platform.
    """

    _debug: bool
    _game: structs.Game
    _last_ping_dt: datetime
    _teams_loaded: bool = False
    _listeners: DefaultDict[str, List[Callable]]

    @property
    def is_ready(self):
        return self._teams_loaded

    @property
    def as_dict(self, kind: Literal["all", "actions"] = "all") -> dict:
        if kind == "all":
            return asdict(self._game)
        elif kind == "actions":
            return asdict(self._game.actions)

    def __init__(self, debug: bool = False) -> None:
        self._game = structs.Game(actions=[])
        self._listeners = defaultdict(list)
        self._debug = debug

    def add_listener(self, message_type: str, func: Callable) -> None:
        """
        Add a callback function to the handling of a specific `message_type`.
        The function must accept one argument of type `structs.Game`.
        """
        self._listeners[message_type].append(func)

    def _receive_ping(self, message: dict) -> None:
        timestamp: str = message.get("timestamp")[:-3]
        self._last_ping_dt = dt_parse(timestamp)

    def _receive_status(self, message: dict) -> None:
        self._game.status = extract(message, "status", structs.GameStatus)
        self._game.current_period = extract(message, "period.current", int)
        self._game.period_status = extract(
            message, "period.periodType", structs.PeriodType
        )
        self._game.clock = extract(message, "clock")
        self._game.shot_clock = extract(message, "shotClock")
        self._game.clock_running = extract(message, "clockRunning", bool)
        self._game.possession = extract(message, "possession", int)
        self._game.possession_arrow = extract(message, "possessionArrow", int)

        # TODO: Handle `scores` value

    def _receive_setup(self, message: dict) -> None:
        pass

    def _receive_match_information(self, message: dict) -> None:
        pass

    def _parse_players(self, players: list[dict]) -> dict[int, structs.Player]:
        player_object_map = {}
        for player in players:
            player_obj = structs.Player(
                pno=extract(player, "pno", int),
                first_name=extract(player, "firstName").strip(),
                last_name=extract(player, "familyName").strip(),
                height=extract(player, "height", float),
                shirt=extract(player, "shirtNumber"),
                position=extract(player, "playingPosition"),
                is_starter=extract(player, "starter", bool),
                is_captain=extract(player, "captain", bool),
                is_active=extract(player, "active", bool),
                stats=structs.PlayerStats(),
            )
            player_object_map[player_obj.pno] = player_obj
        return player_object_map

    def _receive_teams(self, message: dict) -> None:
        teams = message.get("teams")
        for team in teams:
            players = team.get("players")
            parsed_players = self._parse_players(players)
            team_obj = structs.Team(
                number=extract(team, "teamNumber", int),
                name=extract(team, "detail.teamName"),
                code=extract(team, "detail.teamCode"),
                long_code=extract(team, "detail.teamCodeLong"),
                is_home=extract(team, "detail.isHomeCompetitor", bool),
                players=parsed_players,
                game_stats=structs.TeamStats(),
            )
            if team_obj.is_home:
                self._game.home_team = team_obj
            else:
                self._game.away_team = team_obj
        self._teams_loaded = True

    def _parse_players_boxscore(self, team: structs.Team, players: list[dict]) -> None:
        for player in players:
            player_num = extract(player, "pno", int)
            team.players[player_num].stats.update_from_dict(player, strip="s")

    def _receive_boxscore(self, message: dict) -> None:
        teams: list[dict] = message.get("teams")
        for team in teams:
            team_number = team.get("teamNumber")
            team_obj = self._game.get_team_by_number(team_number)
            player_stats = team.get("total").get("players")
            self._parse_players_boxscore(team_obj, player_stats)

    def _receive_action(self, message: dict) -> None:
        action = structs.Action(
            action_number=extract(message, "actionNumber", int),
            team_number=extract(message, "teamNumber", int),
            player_number=extract(message, "pno", int),
            clock=extract(message, "clock"),
            shot_clock=extract(message, "shotClock"),
            time_actual=extract(message, "timeActual", dt_parse),
            period=extract(message, "period", int),
            period_type=extract(message, "periodType", structs.PeriodType),
            action_type=extract(message, "actionType", structs.ActionType.from_str),
            sub_type=extract(message, "subType"),
            qualifiers=message.get("qualifiers", []),
            value=extract(message, "value"),
            previous_action=extract(message, "previousAction", int),
            x=extract(message, "x", float),
            y=extract(message, "y", float),
            area=extract(message, "area"),
            success=extract(message, "success", bool),
        )

        message = compose_action_message(action, self._game)
        self._game.actions.append(action)

        if message != "":
            print(message)

    def _receive_playbyplay(self, message: dict) -> None:
        actions = message.get("actions", [])
        for action in actions:
            try:
                self._receive_action(action)
            except Exception as e:
                logger.error(f"Error handling action in play-by-play.")
                if self._debug:
                    logger.error(action)
                    logger.trace(traceback.format_exc())

    def receive(self, message: dict) -> None:
        """
        Parse a message from the Genius Sports TV feed as json.
        """
        message_type: str = inflection.underscore(message.get("type"))
        if message_type != "ping":
            logger.info(f"Received message type {message_type}")
        handler_name = f"_receive_{message_type}"
        handler: Callable = getattr(self, handler_name, None)
        if handler:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Error handling message type {message_type}")
                if self._debug:
                    logger.error(message)
                    logger.error(traceback.format_exc())
        else:
            logger.error(f"Unknown message type {message_type}")

        listeners = self._listeners[message_type]
        for func in listeners:
            func(self._game)
