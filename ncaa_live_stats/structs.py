from dataclasses import dataclass
from enum import Enum, auto
from typing import Literal, Optional
import inflection
from loguru import logger
from datetime import datetime
from first import first


PERIOD_EXPAND = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}


class AutoEnum(Enum):
    def _generate_next_value_(name, _, __, ___):
        return name


class FromDictMixin:
    @classmethod
    def from_dict(cls, message: dict):
        renamed_dict = {
            inflection.underscore(k.lstrip("s").lstrip("s_")): v.strip() for k, v in message.items()
        }
        return cls(**renamed_dict)

    def update_from_dict(self, message: dict, strip: str = ""):
        annotations = self.__annotations__
        for key, value in message.items():
            normal_key = inflection.underscore(key.lstrip(strip))
            cast_type = annotations.get(normal_key)
            if cast_type is not None:
                cast_value = cast_type(value)
                if cast_value != getattr(self, normal_key):
                    setattr(self, normal_key, cast_value)
            else:
                logger.debug(f"Unknown field {normal_key} found on {self.__class__}")


class StatsMixin:
    @property
    def field_goals_fraction(self) -> str:
        return f"{self.field_goals_made}/{self.field_goals_attempted}"

    @property
    def three_points_fraction(self) -> str:
        return f"{self.three_pointers_made}/{self.three_pointers_attempted}"

    @property
    def free_throws_fraction(self) -> str:
        return f"{self.free_throws_made}/{self.free_throws_attempted}"


@dataclass
class PlayerStats(FromDictMixin, StatsMixin):
    assists: int = 0
    blocks_received: int = 0
    blocks: int = 0
    efficiency: float = 0.0
    fast_break_points_made: int = 0
    field_goals_attempted: int = 0
    field_goals_effective_percentage: float = 0.0
    field_goals_made: int = 0
    field_goals_percentage: float = 0.0
    fouls_coach_disqualifying: int = 0
    fouls_on: int = 0
    fouls_personal: int = 0
    fouls_technical: int = 0
    free_throws_attempted: int = 0
    free_throws_made: int = 0
    free_throws_percentage: float = 0
    minus: int = 0
    minutes: float = 0.0
    plus_minus_points: float = 0.0
    plus: int = 0
    pno: int = 0
    points_fast_break: int = 0
    points_from_turnovers: int = 0
    points_in_the_paint_made: int = 0
    points_in_the_paint: int = 0
    points_second_chance: int = 0
    points: int = 0
    rebounds_defensive: int = 0
    rebounds_offensive: int = 0
    rebounds_total: int = 0
    second_chance_points_attempted: int = 0
    second_chance_points_made: int = 0
    steals: int = 0
    three_pointers_attempted: int = 0
    three_pointers_made: int = 0
    three_pointers_percentage: float = 0.0
    turnovers_percentage: float = 0
    turnovers: int = 0
    two_pointers_attempted: int = 0
    two_pointers_made: int = 0
    two_pointers_percentage: float = 0.0


@dataclass
class TeamStats(FromDictMixin, StatsMixin):
    assists: int = 0
    bench_points: int = 0
    biggest_lead: int = 0
    biggest_scoring_run: int = 0
    blocks_recieved: int = 0
    blocks: int = 0
    efficiency: float = 0.0
    fast_break_points_made: int = 0
    field_goal_percentage: float = 0.0
    field_goals_attempted: int = 0
    field_goals_made: int = 0
    fouls_on: int = 0
    fouls_personal: int = 0
    fouls_team: int = 0
    fouls_technical: int = 0
    free_throws_attempted: int = 0
    free_throws_made: int = 0
    free_throws_percentage: float = 0.0
    lead_changes: float = 0.0
    minutes: float = 0.0
    offensive_rebounds: int = 0
    points_fast_break: int = 0
    points_from_turnovers: int = 0
    points_in_the_paint_made: int = 0
    points_in_the_paint: int = 0
    points_second_chance: int = 0
    points: int = 0
    rebounds_defensive: int = 0
    rebounds_personal: int = 0
    rebounds_team_defensive: int = 0
    rebounds_team_offensive: int = 0
    rebounds_team: int = 0
    rebounds_total_defensive: int = 0
    rebounds_total_offensive: int = 0
    rebounds_total: int = 0
    second_chance_points_made: int = 0
    steals: int = 0
    three_pointers_attempted: int = 0
    three_pointers_made: int = 0
    three_pointers_percentage: float = 0.0
    time_leading: float = 0.0
    times_score_level: int = 0
    turnovers_team: int = 0
    turnovers: int = 0
    two_pointers_attempted: int = 0
    two_pointers_made: int = 0
    two_pointers_percentage: float = 0.0


@dataclass
class TeamScore:
    score: int
    timeouts_remaining: int
    fouls: int
    team_fouls: int


@dataclass
class Player:
    pno: int
    first_name: str
    last_name: str
    height: float
    shirt: str
    position: str
    is_starter: bool
    is_captain: bool
    is_active: bool
    stats: PlayerStats = None

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


@dataclass
class Team:
    number: int = None
    name: str = None
    code: str = None
    long_code: str = None
    is_home: bool = None
    players: dict[int, Player] = None
    game_stats: TeamStats = None
    period_stats: dict[int, TeamStats] = None
    score: TeamScore = None

    def get_player_by_shirt(self, num: int) -> Player:
        return first(self.players.values(), key=lambda p: p.shirt == num)


class GameStatus(AutoEnum):
    READY = auto()
    WARMUP = auto()
    PREMATCH = auto()
    ANTHEM = auto()
    ONCOURT = auto()
    COUNTDOWN = auto()
    INPROGRESS = auto()
    PERIODBREAK = auto()
    INTERUPTTED = auto()
    CANCELLED = auto()
    FINISHED = auto()
    PROTESTED = auto()
    COMPLETE = auto()
    RESCHEDULED = auto()
    DELAYED = auto()


class PeriodType(AutoEnum):
    REGULAR = auto()
    OVERTIME = auto()


class PeriodStatus(AutoEnum):
    PENDING = auto()
    STARTED = auto()
    ENDED = auto()
    CONFIRMED = auto()


class ActionType(AutoEnum):
    GAME = auto()
    PERIOD = auto()
    TWOPT = auto()
    THREEPT = auto()
    FREETHROW = auto()
    JUMPBALL = auto()
    ASSIST = auto()
    BLOCK = auto()
    REBOUND = auto()
    FOUL = auto()
    FOULON = auto()
    TIMEOUT = auto()
    STEAL = auto()
    TURNOVER = auto()
    SUBSTITUTION = auto()
    POSSESSIONCHANGE = auto()
    CLOCK = auto()

    @classmethod
    def from_str(cls, value: str) -> "ActionType":
        value = value.upper().replace("2", "TWO").replace("3", "THREE")
        return cls[value]


@dataclass
class Action:
    action_number: int
    team_number: int
    player_number: int
    clock: str
    shot_clock: str
    time_actual: datetime
    period: int
    period_type: PeriodType
    action_type: ActionType
    sub_type: str
    qualifiers: list[str]
    value: Optional[str]
    x: float
    y: float
    area: str
    success: bool
    previous_action: Optional[int] = None

    @property
    def clock_norm(self) -> str:
        return self.clock[:-3]

    @property
    def period_norm(self) -> str:
        if self.period_type == PeriodType.OVERTIME:
            return "OT" if self.period == 1 else f"OT{self.period}"
        return inflection.ordinalize(self.period)

    @property
    def is_scoring_play(self) -> bool:
        return (
            self.action_type
            in [ActionType.TWOPT, ActionType.THREEPT, ActionType.FREETHROW]
            and self.success
        )

    @property
    def is_non_free_throw_scoring_play(self) -> bool:
        return (
            self.action_type in [ActionType.TWOPT, ActionType.THREEPT] and self.success
        )

    def get_team(self, game: "Game") -> Team:
        return game.get_team_by_number(self.team_number)


@dataclass()
class Game:
    actions: list[Action]
    home_team: Team = None
    away_team: Team = None
    status: GameStatus = None
    current_period: int = None
    period_type: int = None
    period_status: PeriodStatus = None
    clock: str = None
    shot_clock: str = None
    clock_running: bool = None
    possession: Literal[0, 1, 2] = None
    possession_arrow: Literal[0, 1, 2] = None

    def get_team_by_number(self, number: int) -> "Team":
        if self.home_team.number == number:
            return self.home_team
        elif self.away_team.number == number:
            return self.away_team
