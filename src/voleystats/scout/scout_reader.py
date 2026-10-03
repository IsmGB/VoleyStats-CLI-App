import logging
from pandas import DataFrame

from voleystats.scout.models import *

logger = logging.getLogger(__name__)


class ScoutReader:
    _SEP: str = '-'
    _N_SEP: int = 37

    def __init__(self) -> None:
        self._gamesets: list[GameSet] = []
        self._rallies: list[Rally] = []
        self._changes: list[Change] = []
        self._timeouts: list[Timeout] = []
    
        self.gameset_id: int = 0
        self.rotation: Rotation = Rotation(1, 1)
        self.score: Score = (0, 0)

        self._str: str = ""
    

    def __str__(self) -> str:
        return self._str.strip()
    

    def _reset(self) -> None:
        self.score = (0, 0)
        Change.reset()
        Timeout.reset()


    def add_gameset(self, gameset: GameSet) -> None:
        self.gameset_id = gameset.id
        self._gamesets.append(gameset)
        self._reset()

        string = str(gameset)
        sep = self._SEP * max(len(string), self._N_SEP) + '\n'
        self._str += '\n' + sep + string + '\n' + sep
    

    def update_rotation(self, home: int|None = None, away: int|None = None) -> None:
        self.rotation.update(home, away)
        _str = (
            '' if home is None else f"{self.rotation:home}",
            '' if away is None else f"{self.rotation:away}"
        )
        self._str += ' '.join(_str).strip() + '\n'



    def add_technical(self, model: Change|Timeout) -> None:        
        if isinstance(model, Change):
            self._changes.append(model)
        elif isinstance(model, Timeout):
            self._timeouts.append(model)
        self._str += str(model) + '\n'
    

    def add_point(self, point: Point) -> None:
        self.score = point.score
        self._str += str(point) + '\n' + self._SEP * self._N_SEP + '\n'


    def add_rally(self, rally: Rally) -> None:
        self._rallies.append(rally)
        self._str += str(rally) + '\n'
    

    def asdataframe(self) -> DataFrame:
        return DataFrame(
            data=[action for rally in self._rallies for action in rally.astuples()],
            columns=['set', 'team', 'player', 'skill', 'hit', 'ext', 'zone', 'value', 'zHome', 'zAway']
        )