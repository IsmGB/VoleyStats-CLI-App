from dataclasses import dataclass, field, astuple
from abc import ABC, abstractmethod

from typing import ClassVar

from voleystats.enums import *



type Score = tuple[int, int]


@dataclass(slots=True)
class Point:
    team: TeamEnum
    score: Score
    gameset_id: int

    def __post_init__(self) -> None:
        home, away = self.score
        if self.team == TeamEnum.HOME:
            home += 1
        else:
            away += 1
        self.score = (home, away)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(team={self.team.value}, "
            f"score={{'*': {self.score[0]}, 'a': {self.score[1]}}}, "
            f"set_id={self.gameset_id})"
        )
    
    def __str__(self) -> str:
        return f"{self.team.value}p{self.score[0]}:{self.score[1]}"



@dataclass(slots=True)
class Technical(ABC):
    _home: ClassVar[int] = 0
    _away: ClassVar[int] = 0

    team: TeamEnum
    score: Score
    gameset_id: int = field(init=False, default=0)

    def __post_init__(self):
        if self.team == TeamEnum.HOME:
            self.__class__._home += 1
        elif self.team == TeamEnum.AWAY:
            self.__class__._away += 1
    
    @property
    def home(self) -> int:
        return self.__class__._home
    
    @property
    def away(self) -> int:
        return self.__class__._away
    
    @classmethod
    def reset(cls) -> None:
        cls._home = 0
        cls._away = 0
    
    def __getitem__(self, key: TeamEnum) -> int:
        if key == TeamEnum.HOME:
            return self.__class__._home
        if key == TeamEnum.AWAY:
            return self.__class__._away
        return KeyError(key)
    
    @abstractmethod
    def __repr__(self) -> str:
        pass
    
    @abstractmethod
    def __str__(self) -> str:
        pass



class ChangeError(Exception):
    pass



@dataclass(slots=True)
class Change(Technical):
    _MAX: ClassVar[int] = 8

    num_out: int
    num_in: int

    def __post_init__(self) -> None:
        if self[self.team] >= self._MAX:
            raise ChangeError(f"Maximum number of changes exceeded: {self._MAX}")
        super().__post_init__()

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"team='{self.team}', "
            f"change='{self.num_out:>02}:{self.num_in:>02}', "
            f"score='{self.score[0]}:{self.score[1]}', "
            f"set={self.gameset_id})"
        )

    def __str__(self) -> str:
        return f"{self.team}c{self.num_out:>02}:{self.num_in:>02}"



class TimeoutError(Exception):
    pass



@dataclass(slots=True)
class Timeout(Technical):
    _MAX: ClassVar[int] = 2
    
    def __post_init__(self) -> None:
        if self[self.team] >= self._MAX:
            raise TimeoutError(f"Maximum number of timeouts exceeded: {self._MAX}")
        super().__post_init__()
 
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"team='{self.team}', "
            f"score='{self.score[0]}:{self.score[1]}', "
            f"set={self.gameset_id})"
        )
    
    def __str__(self) -> str:
        return f"{self.team}T"



class RotationError(ValueError):
    pass



class Rotation:
    __slots__ = ['_home', '_away']
    _POS: ClassVar[tuple[int, ...]] = (1, 2, 3, 4, 5, 6)

    def __init__(self, home: int, away: int) -> None:
        self.home = home
        self.away = away
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"home={self._home}, away={self._away})"
        )
    
    def __str__(self) -> str:
        return f"*z{self._home} az{self._away}"
    
    def __format__(self, format_spec: str) -> str:
        match format_spec:
            case 'home': return f"*z{self._home}"
            case 'away': return f"az{self._away}"
            case _: return str(self)
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Rotation):
            return NotImplemented
        return (self._home, self._away) == (other._home, other._away)


    @property
    def home(self) -> int:
        return self._home
    
    @home.setter
    def home(self, value: int) -> None:
        if value not in self._POS:
            raise RotationError(f"Invalid home position: {value!r}.")
        self._home = value
    

    @property
    def away(self) -> int:
        return self._away

    @away.setter
    def away(self, value: int) -> None:
        if value not in self._POS:
            raise RotationError(f"Invalid away position: {value!r}.")
        self._away = value
    

    def astuple(self) -> tuple[int, int]:
        return self._home, self._away
    

    def update(self, home: int|None = None, away: int|None = None) -> None:
        if home: self.home = home
        if away: self.away = away



@dataclass(slots=True)
class Action:
    team: TeamEnum
    player: int
    skill: SkillEnum
    hit: HitEnum
    ext: ExtEnum|None
    zone: ZoneEnum|None
    value: ValueEnum

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"team={self.team}, player={self.player}, "
            f"skill={self.skill}, hit={self.hit}, ext={self.ext}, "
            f"zone={self.zone}, value={self.value})"
        )
    
    def __str__(self) -> str:
        action = f"{self.team.value}{self.player:>02d}{self.skill.value}{self.hit.value}{self.value.value}"
        ext = None if self.ext is None else self.ext.value
        zone = None if self.zone is None else self.zone.value
        return f"{action!s:<10}ext={ext!s:<12}zone={zone!s}"


@dataclass(slots=True)
class Rally:
    actions: list[Action]
    point: Point
    rotation: Rotation

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(set={self.gameset_id}, "
            f"rotation={self.rotation!r}, point={self.point!r}, "
            f"actions=[{[repr(action) for action in self.actions]}]"
        )
    
    def __str__(self) -> str:
        return '\n'.join(str(action) for action in self.actions)
    
    @property
    def gameset_id(self) -> int:
        return self.point.gameset_id
    

    def astuples(self) -> list[tuple]:
        home, away = self.rotation.astuple()
        return [
            (self.gameset_id, *astuple(action), home, away)
            for action in self.actions
        ]


@dataclass(slots=True)
class GameSet:
    _count: ClassVar[int] = 0

    name: str|None
    _id: int = field(init=False)


    def __post_init__(self):
        GameSet._count += 1
        self._id = GameSet._count
        if not self.name:
            self.name = f"Set {self._id}"


    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', id='{self._id}')"


    def __str__(self) -> str:
        return f"SET ({self._id}): {self.name}"

    
    @property
    def id(self) -> int:
        return self._id