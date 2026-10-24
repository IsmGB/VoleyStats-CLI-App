import logging
from pydantic import BaseModel, RootModel, Field, field_validator
from pathlib import Path
from typing import Sequence


logger = logging.getLogger(__name__)


class Player(BaseModel):
    name: str = Field(min_length=1)
    surname: str = Field(min_length=1)
    num: int = Field(ge=1, le=99)

    @field_validator('name', 'surname')
    @classmethod
    def to_title(cls, value: str) -> str:
        return value.title()
    
    @property
    def nickname(self) -> str:
        return f"{self.num} {self.surname}, {self.name[0]}."



class Team(RootModel[list[Player]]):
    @property
    def count(self) -> int:
        return len(self.root)
    
    @property
    def players(self) -> Sequence[Player]:
        return self.root
    
    def asdict(self) -> dict[int, str]:
        return {p.num: p.nickname for p in self.root}



def load_team_from_json(jsonfile: str|None) -> Team:
    if jsonfile is None:
        return Team([])
    
    if not (path := Path(jsonfile)).is_file():
        logger.warning("%r could not be opened.", str(path))
        return Team([])
    
    json_text = path.read_text(encoding='utf-8').strip()
    return Team.model_validate_json(json_text) if json_text else Team([])