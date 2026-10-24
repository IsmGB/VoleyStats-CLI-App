import logging
import pandas as pd
from dataclasses import dataclass, field
from pandas._typing import Scalar
from typing import ClassVar

from voleystats.enums import *


logger = logging.getLogger(__name__)


SYMBOLS = list(ValueEnum)


@dataclass
class CoreData:
    df: pd.DataFrame
    teams: TeamsDict[pd.DataFrame] = field(init=False)
    players: TeamsDict[dict[int, pd.DataFrame]] = field(init=False)

    def __post_init__(self) -> None:
        self.df = CoreData._validate_dataframe(self.df)
        self.teams = self._get_teams()
        self.players = self._get_players()
    
    @staticmethod
    def _validate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        COLUMNS = ['set', 'team', 'player', 'skill', 'hit', 'ext', 'zone', 'value', 'zHome', 'zAway']
        if list(df.columns) != COLUMNS:
            raise ValueError(
                f"Inappropriate dataframe strucutre. "
                f"Expected {', '.join(COLUMNS)!r}, got {', '.join(df.columns)!r}"
            )
        if not df['team'].isin(['*', 'a']).all():
            raise ValueError("Column 'team' differs from '*' or 'a'.")
        df['team'] = df['team'].replace({'*': 'home', 'a': 'away'})

        df['set'] = df['set'].astype(dtype=int)
        df['team'] = df['team'].astype(pd.CategoricalDtype(['home', 'away']))
        df['player'] = df['player'].astype(dtype=int)
        df['skill'] = df['skill'].astype(pd.CategoricalDtype(list(SkillEnum)))
        df['hit'] = df['hit'].astype(pd.CategoricalDtype(list(HitEnum)))
        df['ext'] = df['ext'].astype(pd.CategoricalDtype(list(ExtEnum)))
        df['zone'] = df['zone'].astype(pd.CategoricalDtype(list(ZoneEnum)))
        df['value'] = df['value'].astype(pd.CategoricalDtype(SYMBOLS))
        df['zHome'] = df['zHome'].astype(pd.CategoricalDtype([1, 2, 3, 4, 5, 6]))
        df['zAway'] = df['zAway'].astype(pd.CategoricalDtype([1, 2, 3, 4, 5, 6]))
        return df.join(pd.get_dummies(df.pop('value'), dtype=int))
    
    def _get_teams(self) -> TeamsDict[pd.DataFrame]:
        df = self.df.drop(columns='team').groupby(self.df['team'], sort=False, as_index=False)
        return TeamsDict(home=df.get_group('home'), away=df.get_group('away'))
    
    def _get_players(self) -> TeamsDict[dict[int, pd.DataFrame]]:
        home, away = self.teams['home'], self.teams['away']
        return TeamsDict(
            home={int(n): grp for n,grp in home.drop(columns='player').groupby(home['player'], as_index=False)},
            away={int(n): grp for n,grp in away.drop(columns='player').groupby(away['player'], as_index=False)}
        )
    
    def get_numbers(self, team: TeamKey) -> list[int]:
        return list(self.players[team].keys())



class BasicAnalyst:
    _EFF_FORMULA = {
            SkillEnum.ATTACK: lambda df, total: (df['#'] - df[['/', '=']].sum()) / total,
            SkillEnum.BLOCK: lambda df, total: (df[['#', '+']].sum() - df[['/', '=']].sum()) / total,
            SkillEnum.DIG: lambda df, total: df[['#', '+', '/']].sum() / total,
            SkillEnum.SET: lambda df, total: (df[['#', '+']].sum() - df[['/', '=']].sum()) / total,
            SkillEnum.FREE: lambda df, total: (df[['#', '+']].sum() - df[['/', '=']].sum()) / total,
            SkillEnum.RECEIVE: lambda df, total: df[['#', '+']].sum() / total,
            SkillEnum.SERVE: lambda df, total: df[['#', '+', '/', '!']].sum() / total
        }
    PERCENTS = [f"%{s}" for s in SYMBOLS]
    SYMBOLS_PERCENTS = [x for y in zip(SYMBOLS, PERCENTS) for x in y]
    
    @staticmethod
    def get_team(df: pd.DataFrame, team: TeamKey) -> pd.DataFrame:
        return df[df['team'].eq(team)].drop(columns='team')
    
    @staticmethod
    def get_players(df: pd.DataFrame) -> dict[int, pd.DataFrame]:
        return {int(n): grp for n,grp in df.drop(columns='player').groupby(df['player'], as_index=False)}
        
    @staticmethod
    def get_nums(df: pd.DataFrame) -> list[int]:
        return df['player'].unique().tolist()
    
    @staticmethod
    def assign_sum(df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(sum=df[SYMBOLS].sum(axis=1))
    
    @staticmethod
    def filter_by_skill(df: pd.DataFrame, skill: SkillEnum) -> pd.DataFrame:
        return df[df['skill'].eq(skill)]
    
    @classmethod
    def assign_eff_and_per(cls, df: pd.DataFrame, skill: SkillEnum|None=None) -> pd.DataFrame:
        if skill is None:
            func = lambda row: cls._EFF_FORMULA[row['skill']](row[SYMBOLS], row['sum'])
        else:
            func = lambda row: cls._EFF_FORMULA[skill](row[SYMBOLS], row['sum'])

        df = df.copy()
        df['sum'] = df[SYMBOLS].sum(axis=1)
        df['eff'] = df.apply(
            func,
            axis=1
        )
        df[cls.PERCENTS] = df[SYMBOLS].div(df['sum'], axis=0)
        other_cols = [c for c in df.columns if c not in cls.SYMBOLS_PERCENTS]
        return df[other_cols + cls.SYMBOLS_PERCENTS]

    @classmethod
    def concat_eff_and_per(cls, s: pd.Series, skill: SkillEnum) -> pd.Series:
        "Assumes serie of symbols"
        s = s.copy()
        total = s.sum()
        percents = s.div(total)
        percents.index = cls.PERCENTS
        s['sum'] = total
        s['eff'] = cls._EFF_FORMULA[skill](s, total)
        s = pd.concat([s, percents])
        return s[['sum', 'eff'] + cls.SYMBOLS_PERCENTS]
    
    @staticmethod
    def get_values_count(df: pd.DataFrame) -> pd.Series[int]:
        return df[SYMBOLS].sum()
    
    @staticmethod
    def get_symbols_total(df: pd.DataFrame) -> int:
        return df[SYMBOLS].sum().sum()



class TeamsAnalyst:
    ERROR_SKILLS = [skill for skill in SkillEnum if skill != SkillEnum.DIG]
    POINT_SKILLS = [SkillEnum.ATTACK, SkillEnum.BLOCK, SkillEnum.SERVE]

    @staticmethod
    def get_efficiency(df: pd.DataFrame) -> pd.DataFrame:
        df = df.groupby(['set', 'skill'], as_index=False)[SYMBOLS].sum()
        return BasicAnalyst.assign_eff_and_per(df)
    
    @staticmethod
    def get_total_efficiency(df: pd.DataFrame) -> pd.DataFrame:
        df = df.groupby('skill', as_index=False)[SYMBOLS].sum()
        return BasicAnalyst.assign_eff_and_per(df)
    
    @staticmethod
    def get_attack_after_receive(df: pd.DataFrame) -> pd.DataFrame:
        return df[
            (df['skill'] == SkillEnum.ATTACK) &
            (df['skill'].shift(1) == SkillEnum.RECEIVE) &
            (df['team'] == df['team'].shift(1))
        ]
    
    @classmethod
    def get_points_count(cls, df: pd.DataFrame) -> pd.Series[int]:
        return (
            df[df['skill'].isin(cls.POINT_SKILLS) & df['#'].eq(1)]
            .groupby('skill')
            .size()
            .reindex(list(cls.POINT_SKILLS), fill_value=0)
        )
    
    @classmethod
    def get_errors_count(cls, df: pd.DataFrame) -> pd.Series[int]:
        return (
            df[df['skill'].isin(cls.ERROR_SKILLS) & df['='].eq(1)]
            .groupby('skill')
            .size()
            .reindex(list(cls.ERROR_SKILLS), fill_value=0)
        )



class AttackAnalyst:
    TIPS = ExtEnum.get_tips()
    EXT_DIST = ExtEnum.get_distribution()
    
    @staticmethod
    def get_efficiency(df: pd.DataFrame) -> pd.DataFrame:
        df = df.groupby(['hit', 'ext'], as_index=False)[SYMBOLS].sum()
        return BasicAnalyst.assign_eff_and_per(df, SkillEnum.ATTACK)
    
    @staticmethod
    def get_total_efficiency(df: pd.DataFrame) -> pd.Series:
        return BasicAnalyst.concat_eff_and_per(df[SYMBOLS].sum(), SkillEnum.ATTACK)
    
    @staticmethod
    def get_ext_totals(df: pd.DataFrame) -> pd.Series:
        df = df.assign(label=df['ext'].where(df['ext'].notna(), df['hit']))
        df = df.groupby('label', sort=False)[SYMBOLS].sum()
        return df[SYMBOLS].sum(axis=1)

    @staticmethod
    def get_ext_count(df: pd.DataFrame, ext: set[ExtEnum]) -> pd.DataFrame:
        df = df[df['ext'].isin(ext)]
        df = df.assign(sum=df[SYMBOLS].sum(axis=1))
        return (
            df.groupby(['ext', 'zone'], as_index=False)
            .agg(count=('sum', 'sum'), err_count=('=', 'sum'))
            .assign(
                per=lambda df: df['count'] / df['count'].sum(),
                err_per=lambda df: df['err_count'] / df['err_count'].sum()
            )
        )
    
    @classmethod
    def get_error_percent(cls, df: pd.DataFrame, net: int) -> float:
        df = df[df['ext'].isin(cls.EXT_DIST[net] - cls.TIPS)]
        total = df[SYMBOLS].sum()
        return total['='] / total.sum()
    
    @classmethod
    def get_tip_percent(cls, df: pd.DataFrame, net: int) -> float:
        symbols = df[SYMBOLS]
        ext = cls.EXT_DIST[net]
        total = symbols[df['ext'].isin(ext)].sum().sum()
        tips = symbols[df['ext'].isin(cls.TIPS & ext)].sum().sum()
        return tips / total



class ServeAnalyst:
    @staticmethod
    def get_efficiency(df: pd.DataFrame) -> pd.DataFrame:
        df = df.groupby(['hit', 'ext'], as_index=False)[SYMBOLS].sum()
        return BasicAnalyst.assign_eff_and_per(df, SkillEnum.SERVE)
    
    @staticmethod
    def get_total_efficiency(df: pd.DataFrame) -> pd.Series:
        return BasicAnalyst.concat_eff_and_per(df[SYMBOLS].sum(), SkillEnum.SERVE)
    
    @staticmethod
    def get_values_per_hit(df: pd.DataFrame) -> pd.DataFrame:
        return df.groupby('hit', as_index=False)[SYMBOLS].sum()




class ReceiveAnalist:
    @staticmethod
    def keep_rotation(df: pd.DataFrame, team: TeamKey) -> pd.DataFrame:
        to_keep, to_drop = ('zHome', 'zAway') if team == 'home' else ('zAway', 'zHome')
        return df.drop(columns=to_drop).rename(columns={to_keep: 'rotation'})
    
    @staticmethod
    def get_serve_receive(df: pd.DataFrame, team: TeamKey) -> pd.DataFrame:
        receive = df['team'].eq(team) & df['skill'].eq(SkillEnum.RECEIVE)
        return df[receive].assign(serve_ply=df['player'].shift(1)[receive].astype('int64')).reset_index(drop=True)
    
    @staticmethod
    def get_efficiency(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
        rot_df = df.groupby(['hit', 'rotation'], as_index=False)[SYMBOLS].sum()
        hit_df = df.groupby('hit', as_index=False)[SYMBOLS].sum()
        return {
            'rotation': BasicAnalyst.assign_eff_and_per(rot_df, SkillEnum.RECEIVE),
            'total': BasicAnalyst.assign_eff_and_per(hit_df, SkillEnum.RECEIVE)
        }
    
    @staticmethod
    def get_total_efficiency(df: pd.DataFrame) -> dict:
        rot_df = df.groupby('rotation', as_index=False)[SYMBOLS].sum()
        return {
            'rotation': BasicAnalyst.assign_eff_and_per(rot_df, SkillEnum.RECEIVE),
            'total': BasicAnalyst.concat_eff_and_per(df[SYMBOLS].sum(), SkillEnum.RECEIVE)
        }
    
    @staticmethod
    def group_by_serve(df: pd.DataFrame) -> pd.DataFrame:
        return df.groupby('serve_ply')[SYMBOLS].sum()
    
    @staticmethod
    def group_by_zone(df: pd.DataFrame) -> pd.DataFrame:
        return df.groupby('zone', as_index=False)[SYMBOLS].sum()