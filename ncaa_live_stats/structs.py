from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Literal
import inflection


class AutoEnum(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name


class CreateFromDictMixin:
    @classmethod
    def from_dict(cls, message: dict):
        renamed_dict = {
            inflection.underscore(k.lstrip("s")): v
            for k, v in message.items()
        }
        return cls(**renamed_dict)


@dataclass
class PlayerStats:
    assists: int
    blocks: int
    blocks_recieved: int
    efficiency: float
    fast_break_points_made: int
    field_goals_attempted: int
    field_goals_made: int
    field_goals_percentage: float
    fouls_on: int
    fouls_personal: int
    fouls_technical: int
    free_throws_attempted: int
    free_throws_made: int
    free_throws_percentage: float
    minutes: float
    plus_minus_points: float
    points: int
    points_fast_break: int
    points_from_turnovers: int
    points_in_the_paint: int
    points_in_the_paint_made: int
    points_second_chance: int
    rebounds_defensive: int
    rebounds_offensive: int
    rebounds_total: int
    second_chance_points_made: int
    steals: int
    three_pointers_attempted: int
    three_pointers_made: int
    three_pointers_percentage: float
    turnovers: int
    two_pointers_attempted: int
    two_pointers_made: int
    two_pointers_percentage: float


@dataclass
class TeamStats:
    assists: int
    bench_points: int
    biggest_lead: int
    biggest_scoring_run: int
    blocks: int
    blocks_recieved: int
    efficiency: float
    fast_break_points_made: int
    points_from_turnovers: int
    field_goals_attempted: int
    field_goals_made: int
    field_goal_percentage: float
    fouls_on: int
    fouls_personal: int
    fouls_team: int
    fouls_technical: int
    free_throws_attempted: int
    free_throws_made: int
    free_throws_percentage: float
    lead_changes: float
    minutes: float
    points: int
    points_fast_break: int
    points_in_the_paint: int
    points_in_the_paint_made: int
    points_second_chance: int
    rebounds_defensive: int
    offensive_rebounds: int
    rebounds_personal: int
    rebounds_team: int
    rebounds_team_defensive: int
    rebounds_team_offensive: int
    rebounds_total: int
    rebounds_total_defensive: int
    rebounds_total_offensive: int
    second_chance_points_made: int
    steals: int
    three_pointers_attempted: int
    three_pointers_made: int
    three_pointers_percentage: float
    time_leading: float
    times_score_level: int
    turnovers: int
    turnovers_team: int
    two_pointers_attempted: int
    two_pointers_made: int
    two_pointers_percentage: float
    


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


@dataclass
class Team:
    number: int
    name: str
    code: str
    long_code: str
    is_home: bool
    players: list[Player]
    game_stats: TeamStats = None
    period_stats: dict[int, TeamStats] = None
    score: TeamScore = None


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


@dataclass()
class Game:
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