import pandas as pd
from abc import ABC
from dataclasses import dataclass, field
from typing import Any

from voleystats.enums import ValueEnum, SkillEnum, TeamsDict, HitEnum


class Mapper(ABC):
    @staticmethod
    def map_efficiency(df: pd.DataFrame) -> list[tuple]:
        return list(df.itertuples(index=False, name=None))
    
    @staticmethod
    def map_total_efficiency(df: pd.Series) -> tuple:
        return tuple(df.to_list())



class TeamMapper:
    @staticmethod
    def map_efficiency(df: pd.DataFrame) -> dict[Any, list[tuple]]:
        df['skill'] = df['skill'].map(lambda x: x.name if isinstance(x, SkillEnum) else x)
        return {
            s: [tuple(values) for _, *values in grp.itertuples(index=False, name=None)]
            for s, grp in df.groupby('set', sort=False)
        }
    
    @staticmethod
    def map_total_efficiency(df: pd.DataFrame) -> list[tuple]:
        df['skill'] = df['skill'].map(lambda x: x.name if isinstance(x, SkillEnum) else x)
        return list(df.itertuples(index=False, name=None))




class AttackMapper(Mapper):
    pass



class ServeMapper(Mapper):
    pass



class ReceiveMapper:
    @staticmethod
    def map_efficiency(d: dict[str, pd.DataFrame]) -> dict[HitEnum, dict]:
        return {
            hit: {
                'rotations': [rot for _, *rot in d['rotation'].itertuples(index=False, name=None)],
                'total': values
            } for hit, *values in d['total'].itertuples(index=False, name=None)
        }
    
    @staticmethod
    def map_total_efficiency(d: dict[str, Any]) -> dict:
        return {
            'rotations': list(d['rotation'].itertuples(index=False, name=None)),
            'total': d['total'].to_list()
        }