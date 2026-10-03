from typing import Any

from voleystats.scout.scout_reader import ScoutReader
from voleystats.scout.models import *

# INNECESARIO
class ParserToScout:
    @staticmethod
    def gameset(name: str) -> GameSet:
        return GameSet(name=name)

    @staticmethod
    def changes(team: TeamEnum, changes: list[tuple[int,int]], score: Score) -> list[Change]:
        return [
            Change(team=team, score=score, num_out=num_out, num_in=num_in)
            for num_out, num_in in changes
        ]
    
    @staticmethod
    def rotation(home: int, away: int) -> Rotation:
        return Rotation(home=home, away=away)
    
    @staticmethod
    def timeout(team: TeamEnum, score: Score) -> Timeout:
        return Timeout(team=team, score=score)
    
    @staticmethod
    def point(team: TeamEnum, score: Score, gameset_id: int) -> Point:
        return Point(team=team, score=score, gameset_id=gameset_id)
    
    @staticmethod
    def rally(actions: list[Action], point: Point, rotation: Rotation) -> Rally:
        return Rally(actions=actions, point=point, rotation=rotation)