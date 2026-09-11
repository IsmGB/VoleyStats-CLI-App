from dataclasses import dataclass, field, InitVar, asdict, astuple
from typing import ClassVar, Optional, Any
from enum import StrEnum
from abc import ABC


class NmonTeam(StrEnum):
    HOME = '*'
    AWAY = 'a'
    COMBO = '.'

class NmonSkill(StrEnum):
    ATTACK = 'A'
    BLOCK = 'B'
    DIG = 'D'
    SET = 'E'
    FREE = 'F'
    RECEIVE = 'R'
    SERVE = 'S'

class NmonHit(StrEnum):
    # FAST = 'F'
    HIGH = 'H'
    MEDIUM = 'M'
    FAST = 'N' # zaguero
    OTHER = 'O'
    QUICK = 'Q'
    TENSE = 'T'
    SUPER = 'U'

class NmonValue(StrEnum):
    PERFECT = '#'
    POSITIVE = '+'
    EXCLAMATIVE = '!'
    NEGATIVE = '-'
    SLASH = '/'
    ERROR = '='

class NmonExt(StrEnum):
    X1 = 'X1'
    X2 = 'X2'
    X3 = 'X3'
    X4 = 'X4'
    X5 = 'X5'
    X6 = 'X6'
    X7 = 'X7'
    X8 = 'X8'
    X9 = 'X9'
    K1 = 'K1'
    K2 = 'K2'
    K3 = 'K3'
    K4 = 'K4'
    K5 = 'K5'
    K6 = 'K6'
    K7 = 'K7'
    K8 = 'K8'
    K9 = 'K9'
    NONE = ''

class NmonZone(StrEnum):
    Z1 = 'Z1'
    Z2 = 'Z2'
    Z3 = 'Z3'
    Z4 = 'Z4'
    Z5 = 'Z5'
    Z6 = 'Z6'
    Z7 = 'Z7'
    Z8 = 'Z8'
    Z9 = 'Z9'
    NONE = ''

type TeamDict[T] = dict[NmonTeam, T]

type ExcelExport = tuple[int, TeamDict[int], str, int, str, str, str, str, str]

# VALUES_DICT: dict[NmonValue, NmonValue] = { # Hacer un diccionario específico para cada skill
#     NmonValue.PERFECT: NmonValue.ERROR,
#     NmonValue.POSITIVE: NmonValue.NEGATIVE,
#     NmonValue.SLASH: NmonValue.SLASH,
#     NmonValue.NEGATIVE: NmonValue.POSITIVE,
#     NmonValue.ERROR: NmonValue.PERFECT,
#     NmonValue.EXCLAMATIVE: NmonValue.EXCLAMATIVE
# }

VALUES_DICT:  dict[NmonSkill, dict[NmonValue, NmonValue]] = {
    NmonSkill.BLOCK: {
        NmonValue.PERFECT: NmonValue.SLASH,
        NmonValue.POSITIVE: NmonValue.NEGATIVE,
        NmonValue.SLASH: NmonValue.POSITIVE,
        NmonValue.NEGATIVE: NmonValue.POSITIVE,
        NmonValue.ERROR: NmonValue.PERFECT,
        NmonValue.EXCLAMATIVE: NmonValue.EXCLAMATIVE
    },
    NmonSkill.DIG: {
        NmonValue.PERFECT: NmonValue.NEGATIVE,
        NmonValue.POSITIVE: NmonValue.NEGATIVE,
        NmonValue.SLASH: NmonValue.POSITIVE,
        NmonValue.NEGATIVE: NmonValue.POSITIVE,
        NmonValue.ERROR: NmonValue.PERFECT,
        NmonValue.EXCLAMATIVE: NmonValue.NEGATIVE
    },
    NmonSkill.RECEIVE: {
        NmonValue.PERFECT: NmonValue.NEGATIVE,
        NmonValue.POSITIVE: NmonValue.NEGATIVE,
        NmonValue.SLASH: NmonValue.SLASH,
        NmonValue.NEGATIVE: NmonValue.POSITIVE,
        NmonValue.ERROR: NmonValue.PERFECT,
        NmonValue.EXCLAMATIVE: NmonValue.EXCLAMATIVE
    },
}

SKILLS_DICT: dict[NmonSkill, NmonSkill] = {
    NmonSkill.ATTACK: NmonSkill.BLOCK,
    NmonSkill.SERVE: NmonSkill.RECEIVE
}



@dataclass(slots=True)
class GameSet:
    _count: ClassVar[int] = 0

    name: Optional[str]
    _points: list[tuple[int,int]] = field(init=False)
    _id: int = field(init=False)


    def __post_init__(self):
        GameSet._count += 1
        self._id = GameSet._count
        if not self.name:
            self.name = f"Set {self._id}"
        self._points = [(0, 0)]
    

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', id='{self._id}')"
    

    def add_point(self, team: NmonTeam) -> None:
        home, away = self._points[-1]
        if team == NmonTeam.HOME:
            self._points.append((home + 1, away))
        elif team == NmonTeam.AWAY:
            self._points.append((home, away + 1))

    
    @property
    def id(self) -> int:
        return self._id
    

    @property
    def points(self) -> list[tuple[int, int]]:
        return self._points



@dataclass(slots=True)
class BaseEvent(ABC):
    _home: ClassVar[int] = 0
    _away: ClassVar[int] = 0

    team: NmonTeam
    score: TeamDict[int] = field(init=False)
    gameset_id: int = field(init=False, default=0)


    def __post_init__(self):
        if self.team == NmonTeam.HOME:
            self.__class__._home += 1
        elif self.team == NmonTeam.AWAY:
            self.__class__._away += 1
        self.score = {NmonTeam.HOME: 0, NmonTeam.AWAY: 0}



@dataclass(slots=True)
class Change(BaseEvent):
    num_out: int
    num_in: int

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"team='{self.team}', "
            f"change='{self.num_out:>02}:{self.num_in:>02}', "
            f"score='{self.score[NmonTeam.HOME]}:{self.score[NmonTeam.AWAY]}', "
            f"set={self.gameset_id})"
        )


@dataclass(slots=True)
class Timeout(BaseEvent):
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"team='{self.team}', "
            f"score='{self.score[NmonTeam.HOME]}:{self.score[NmonTeam.AWAY]}', "
            f"set={self.gameset_id})"
        )


@dataclass(slots=True)
class SingleAction:
    nmons: InitVar[tuple[str, ...]]
    team: NmonTeam = field(init=False)
    player: int = field(init=False)
    _skill: Optional[NmonSkill] = field(init=False)
    hit: Optional[NmonHit] = field(init=False)
    _value: NmonValue = field(init=False)
    zone: Optional[NmonZone] = field(init=False)
    ext: Optional[NmonExt] = field(init=False)


    def __post_init__(self, nmons: tuple[str, ...]) -> None:
        self.team = NmonTeam(nmons[0] or NmonTeam.HOME)
        self.player = int(nmons[1])
        self._skill = NmonSkill(nmons[2]) if nmons[2] else None
        self.zone = NmonZone(nmons[4]) if nmons[4] else None
        self._value = NmonValue(nmons[5] or NmonValue.POSITIVE)

        if hit:=nmons[3]:
            if hit[0] in 'HQT':
                self.ext = NmonExt(('K' if hit[0] == 'Q' else 'X') + hit[-1]) if hit[-1].isnumeric() else None
                self.hit = NmonHit(hit[0])
            elif hit[0] in 'KX':
                self.ext = NmonExt(hit)
                self.hit = NmonHit.QUICK if hit[0] == 'K' else NmonHit.HIGH
            else:
                self.ext = None
                self.hit = NmonHit(hit[0])
        else:
            self.ext = None
            self.hit = None
    

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code='{self}', ext='{self.ext}', zone='{self.zone}')"
    

    def __str__(self) -> str:
        return f"{self.team}{self.player:>02}{self.skill}{self.hit}{self.value}"
    

    def complete_as_single(self) -> None:
        if self._skill is None:
            self._skill = NmonSkill.ATTACK
        if self.hit is None:
            self.hit = NmonHit.HIGH
    

    def complete_as_combo(self, prev: SingleAction) -> None:
        self.team = NmonTeam.HOME if prev.team == NmonTeam.AWAY else NmonTeam.AWAY
        if self._skill is None and prev.skill:
            self._skill = SKILLS_DICT[prev.skill]
        self.hit = prev.hit
        self.zone = prev.zone
        self.ext = prev.ext
    

    @property
    def value(self) -> NmonValue:
        return self._value
    
    @value.setter
    def value(self, value: NmonValue) -> None:
        self._value = value
    
    @property
    def skill(self) -> NmonSkill:
        if self._skill:
            return self._skill
        raise ValueError("Skill was not found.")
    
    @skill.setter
    def skill(self, value: NmonSkill) -> None:
        self._skill = value
    

    

@dataclass(slots=True)
class FullAction:
    gameset_id: int
    rotation: TeamDict[int]
    action: InitVar[SingleAction]
    team: NmonTeam = field(init=False)
    player: int = field(init=False)
    skill: NmonSkill = field(init=False)
    hit: NmonHit = field(init=False)
    value: NmonValue = field(init=False)
    ext: NmonExt = field(init=False)
    zone: NmonZone = field(init=False)


    def __post_init__(self, action: SingleAction) -> None:
        self.team = NmonTeam(action.team)
        self.player = action.player
        self.skill = NmonSkill(action.skill)
        self.hit = NmonHit(action.hit)
        self.value = NmonValue(action.value)
        self.ext = NmonExt(action.ext or NmonExt.NONE)
        self.zone = NmonZone(action.zone or NmonZone.NONE)
    

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"set={self.gameset_id}, "
            f"rotation={{'*': {self.rotation[NmonTeam.HOME]}, 'a': {self.rotation[NmonTeam.AWAY]}}}, "
            f"action=(code='{self}', ext='{self.ext.value}', zone='{self.zone.value}'))"
        )


    def __str__(self) -> str:
        return f"{self.team.value}{self.player:>02}{self.skill.value}{self.hit.value}{self.value.value}"
    

    def asdict(self) -> dict[str, int | str]:
        return asdict(self)
        return {
            'Set': self.gameset_id,
            '*z': self.rotation[NmonTeam.HOME],
            'az': self.rotation[NmonTeam.AWAY],
            'Team': self.team,
            'Player': self.player,
            'Skill': self.skill,
            'Hit': self.hit,
            'Value': self.value,
            'Ext.': self.ext,
            'Zone': self.zone
        }
    

    def astuple(self) -> ExcelExport:
        return astuple(self)