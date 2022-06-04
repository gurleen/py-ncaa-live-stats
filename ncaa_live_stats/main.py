from . import structs
from datetime import datetime
from dateutil.parser import parse as dt_parse
from typing import Any, Callable, TypeVar
from loguru import logger
import inflection
import traceback


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
    _game: structs.Game
    _last_ping_dt: datetime

    def __init__(self) -> None:
        pass

    def _receive_ping(self, message: dict) -> None:
        timestamp: str = message.get("timestamp")[:-3]
        self._last_ping_dt = dt_parse(timestamp)

    def _receive_status(self, message: dict) -> None:
        self._game.status = extract(message, "status", structs.GameStatus)
        self._game.current_period = extract(message, "period.current", int)
        self._game.period_status = extract(message, "period.periodType", structs.PeriodType)
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

    def _parse_players(self, players: list[dict]) -> list[structs.Player]:
        player_object_list = []
        for player in players:
            player_obj = structs.Player(
                pno=extract(player, "pno", int),
                first_name=extract(player, "firstName"),
                last_name=extract(player, "familyName"),
                height=extract(player, "height", float),
                shirt=extract(player, "shirtNumber"),
                position=extract(player, "playingPosition"),
                is_starter=extract(player, "starter", bool),
                is_captain=extract(player, "captain", bool),
                is_active=extract(player, "active", bool)
            )
            player_object_list.append(player_obj)
        return player_object_list

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
                players=parsed_players
            )
            if team_obj.is_home:
                self._game.home_team = team_obj
            else:
                self._game.away_team = team_obj


    def receive(self, message: dict) -> None:
        message_type: str = inflection.underscore(message.get("type"))
        handler_name = f"_receive_{message_type}"
        handler: Callable = getattr(self, handler_name, None)
        if handler:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Error handling message type {message_type}")
                print(traceback.format_exc())
        else:
            logger.error(f"Unknown message type {message_type}")