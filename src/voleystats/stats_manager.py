import pandas as pd

from voleystats.data_classes import *


class StatsManager:
    def __init__(self) -> None:
        self._gamesets: list[GameSet] = []
        self._actions: list[FullAction] = []
        self._changes: list[Change] = []
        self._timeouts: list[Timeout] = []
        self._repr: str = ''

        self.current_gameset: Optional[GameSet] = None
        self.current_rotation: TeamDict[int] = {NmonTeam.HOME: 0, NmonTeam.AWAY: 0}
        self.current_point: TeamDict[int] = {NmonTeam.HOME: 0, NmonTeam.AWAY: 0}
    

    def __repr__(self) -> str:
        return self._repr

    
    def add_gameset(self, gameset: GameSet) -> None:
        if self.current_gameset:
            self._gamesets.append(gameset)
        self.current_gameset = gameset
        self._repr += repr(gameset) + '\n'
    

    def add_event(self, event: BaseEvent) -> None:
        if not self.current_gameset:
            return
        
        event.score = self.current_point
        event.gameset_id = self.current_gameset.id
        
        if isinstance(event, Change):
            self._changes.append(event)
        elif isinstance(event, Timeout):
            self._timeouts.append(event)
        self._repr += repr(event) + '\n'
    

    def set_rotation(self, rotation: TeamDict[int]) -> None:
        for k,v in rotation.items():
            if v:
                self.current_rotation[k] = v
        # self._repr += repr(rotation) + '\n'
        self._repr += f"{{'*': {rotation[NmonTeam.HOME]}, 'a': {rotation[NmonTeam.AWAY]}}}\n"
    

    def add_codes(self, codes: list[SingleAction]) -> None:
        if not self.current_gameset:
            return
        
        rally = [
            FullAction(
                gameset_id=self.current_gameset.id,
                rotation=self.current_rotation.copy(),
                action=code
            ) for code in codes
        ]
        self._actions.extend(rally)
        for item in rally:
            self._repr += repr(item) + '\n'
    

    def add_point(self, team: NmonTeam) -> None:
        if self.current_gameset:
            self.current_gameset.add_point(team)
            a, b = self.current_gameset.points[-1]
            self.current_point = {NmonTeam.HOME: a, NmonTeam.AWAY: b}
            self._repr += repr(team.value) + '\n'
    
    
    def asdataframe(self) -> pd.DataFrame:
        return pd.DataFrame([action.astuple() for action in self._actions])