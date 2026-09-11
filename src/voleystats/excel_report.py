import xlsxwriter as xlsx
from xlsxwriter.worksheet import Worksheet
from xlsxwriter.workbook import Format
import pandas as pd
from pandas._typing import Scalar
import numpy as np
from pathlib import Path
from enum import StrEnum
from typing import Self, cast, Callable, Iterable, Sequence, TypedDict, Literal
from dataclasses import dataclass, field
from io import BytesIO

from voleystats.data_classes import *
from voleystats.graphs import CourtFigure, PieFigure, BarFigure, get_color_shades


Symbol = Literal["#", "+", "!", "-", "/", "="]
Lead = Literal['Team', 'Player']
Teams = Literal['home', 'away']


# class Teams(StrEnum):
#     HOME = 'home'
#     AWAY = 'away'


class Sheet(StrEnum):
    SUMMARY = 'Summary'
    HOME_DATA = 'Home summary'
    AWAY_DATA = 'Away summary'
    HOME_ATTACK = 'Home ATTACK'
    HOME_SERVE = 'Home SERVE'
    HOME_RECEIVE = 'Home RECEIVE'
    AWAY_ATTACK = 'Away ATTACK'
    AWAY_SERVE = 'Away SERVE'
    AWAY_RECEIVE = 'Away RECEIVE'
    OBJETIVES = 'Objetives'


class ExcelReport:
    DF_COLUMNS = ['set', 'team', 'num', 'skill', 'hit', 'value', 'ext', 'zone', 'home_rot', 'away_rot']
    EFF_FORMULA = {
            NmonSkill.ATTACK: lambda df, total: (df['#'] - df[['/', '=']].sum()) / total,
            NmonSkill.BLOCK: lambda df, total: (df[['#', '+']].sum() - df[['/', '=']].sum()) / total,
            NmonSkill.DIG: lambda df, total: df[['#', '+', '/']].sum() / total,
            NmonSkill.SET: lambda df, total: (df[['#', '+']].sum() - df[['/', '=']].sum()) / total,
            NmonSkill.FREE: lambda df, total: (df[['#', '+']].sum() - df[['/', '=']].sum()) / total,
            NmonSkill.RECEIVE: lambda df, total: df[['#', '+']].sum() / total,
            NmonSkill.SERVE: lambda df, total: df[['#', '+', '/', '!']].sum() / total
        }
    COLORS: dict[str, Any] = {
        'symbols': ["#077237", '#66C24A', '#FFD966', "#E6A056", '#E06666', "#8D0808"],
        'error': '#cc0000',
        'point': '#009900',
        'skill_point': ["#D1FAE5", "#059669", "#065F46"],
        'skill_error': ["#FEE2E2", "#FCA5A5", "#F87171", "#EF4444", "#DC2626", "#991B1B"],
        # 'skill_error': ["#FEE2E2", "#FCA5A5", "#F87171", "#DC2626", "#991B1B"],
        'court_bg': ["#ad7d7d", "#ffffff"],
        'players': [
            "#E6194B",
            "#3CB44B",
            "#4363D8",
            "#F58231",
            "#911EB4",
            "#42D4F4",
            "#F032E6",
            "#BFEF45",
            "#FABED4",
            "#469990",
            "#DCBEFF",
            "#9A6324",
            "#FFE119",
            "#800000",
        ]

    }
    MIN_REPS = {
        'attack': 2,
        'attack_distribution': 2,
        'attack_defender': 2,
        'serve': 2,
        'serve_hit': 2,
        'receive': 2,
        'receive_serve': 2,
        'receive_zone': 2
    }
    

    def __init__(self, excelfile: Path, df: pd.DataFrame, players: dict[str, dict[int,dict[str,str]]|None]={}):
        def import_df(df: pd.DataFrame) -> pd.DataFrame:
            df[2] = df[2].replace({e.value: e.name.lower() for e in NmonTeam})
            df = df.join(df[1].apply(pd.Series)).drop(columns=1)
            df.columns = ExcelReport.DF_COLUMNS
            return df
        
        def build_groups(df: pd.DataFrame) -> dict[Teams, dict[Scalar, Any]]:
            # Dataframe shaping
            df = df.join(df[1].apply(pd.Series)).drop(columns=1)
            df.columns = self.DF_COLUMNS
            df = df.join(
                pd.get_dummies(
                    df.pop('value').astype(pd.CategoricalDtype(categories=self._value_symbols)),
                    dtype=int
                )
            )
            receive_cond = lambda team: (df['team'] == team) & (df['skill'] == NmonSkill.RECEIVE)
            # Group by team and nums
            return {
                cast(Teams, team): {
                    team: team_group.drop(columns='team'),
                    'num': {num: num_group.drop(columns=['team', 'num']) for num, num_group in team_group.groupby('num', as_index=False)},
                    'receive' : df[receive_cond(team)|receive_cond(team).shift(-1, fill_value=False)]
                } for team, team_group in df.groupby('team', as_index=False)
            }
        
        def define_players(names: dict[str, dict[int, dict[str,str]]|None]) -> dict[Teams, dict[int,str]]:
            # List of nums for each team
            nums = {team: list(self.groups[team]['num'].keys()) for team in ('home', 'away')}
            return {
                team: {} if names.get(team) is None else {
                    n: f"{n} {name['surname'].upper()}, {name['name'][0].upper()}."
                    for n in nums[team] if (name := names[team].get(n)) # type: ignore
                } for team in ('home', 'away')
            }
        
        def get_eff_value_list() -> list[str]:
            value_headers = [(v, f'%{v}') for v in self._value_symbols]
            return ["Tot.", "%Eff.", *[x for y in value_headers for x in y]]
    
        self.excelfile = excelfile
        self.df = import_df(df)

        self._value_symbols: list[Symbol] = [e.value for e in NmonValue]
        self._eff_header = get_eff_value_list()

        self.groups = build_groups(df)
        self.players = define_players(players)


    def __enter__(self) -> Self:
        self.workbook = xlsx.Workbook(self.excelfile)        
        self.worksheets: dict[str, Worksheet] = {}

        FORMATS: dict[str, dict[str, Any]] = {
            'header': {
                'bold': True,
                'font_size': 12,
                'font_color': '#ffffff',
                'bg_color': '#0070C0',
                'border': 1,
                'num_format': '@'
            },
            'blank': {
                'bg_color': '#ffffff'
            }
        }
        FORMATS_LIST: dict[str, tuple[dict[str, Any], ...]] = {
            'data': (
                {
                    'bg_color': "#BFDCF1",
                    'border': 1
                },
                {
                    'bg_color': "#81C3F1",
                    'border': 1
                }
            ),
            'merge': (
                {
                    'valign': 'top',
                    'border': 1,
                    'bg_color': "#BFDCF1"
                },
                {
                    'valign': 'top',
                    'border': 1,
                    'bg_color': "#81C3F1"
                }
            ),
            'percent': (
                {
                    'bg_color': "#BFDCF1",
                    'border': 1,
                    'num_format': "0.00%"
                },
                {
                    'bg_color': "#81C3F1",
                    'border': 1,
                    'num_format': "0.00%"
                }
            )
        }

        self.formats = {k: self.workbook.add_format(v) for k, v in FORMATS.items()}
        self.formats_list = {k: [self.workbook.add_format(item) for item in v] for k, v in FORMATS_LIST.items()}

        return self
    

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.workbook.close()
        return False
    

    def __repr__(self) -> str:
        return str(self.df)
    

    def _new_worksheet(self, ws_name: str) -> Worksheet:
        worksheet = self.workbook.add_worksheet(ws_name)
        self.worksheets.update({ws_name: worksheet})
        return worksheet


    def _write_header(self, ws: Worksheet, row: int, col: int, columns: list[str], cell_format: Optional[Format]=None) -> None:
        ws.write_row(row, col, columns, cell_format)
        try:
            idx = columns.index(NmonValue.ERROR)
        except ValueError:
            return
        ws.write_string(row, col + idx, NmonValue.ERROR, cell_format)
    

    def build_worksheet_data(self, ws_team: Optional[Teams]=None) -> None:
        def iterate_over_skills(df: pd.DataFrame) -> None:
            nonlocal row
            for skill, *values in df.itertuples(index=False, name=None):
                efficiency = self._get_efficiency(skill, pd.Series(values, index=symbols))
                worksheet.write_row(row, 2, [skill.name, *efficiency], frmts['data'][row%2])
                row += 1
        # Variables setup
        symbols = self._value_symbols
        frmt, frmts = self.formats, self.formats_list
        fig_pie = PieFigure()
        fig_bar = BarFigure()

        skills_to_error = list(NmonSkill)
        skills_to_error.remove(NmonSkill.DIG)
        skills_to_point = [NmonSkill.ATTACK, NmonSkill.BLOCK, NmonSkill.SERVE]
        
        # Worksheet setup
        if ws_team is None:
            ws_name = Sheet.SUMMARY
            lead = 'Team'
            data = {team: self.groups[team][team] for team in ('home', 'away')}
            names = {'home': 'Home', 'away': 'Away'}
        elif ws_team == 'home':
            ws_name = Sheet.HOME_DATA
            lead = 'Player'
            data = self.groups[ws_team]['num']
            names = self.players[ws_team]
        elif ws_team == 'away':
            ws_name = Sheet.AWAY_DATA
            lead = 'Player'
            data = self.groups[ws_team]['num']
            names = self.players[ws_team]
        else:
            raise ValueError()

        worksheet = self._new_worksheet(ws_name)
        # worksheet.freeze_panes(1, 0)
        worksheet.set_column(0, 0, self._get_fit_width(list(names.values())))
        # self._write_header(worksheet, 0, 0, [lead, "Set", "Skill", *self._eff_header], frmt['header'])
        # Write worksheet
        row, merge_key, merge_s = 0, 1, 1
        for key, data_df in data.items():
            self._write_header(worksheet, row, 0, [lead, "Set", "Skill", *self._eff_header], frmt['header'])
            row += 1
            key = cast(Any, key)
            name = names.get(key, key)
            team_start = row
            df = data_df.groupby(['set', 'skill'], as_index=False)[symbols].sum()
            # Write sets
            for s, set_df in df.groupby('set', sort=False)[['skill', *symbols]]:
                set_start = row
                iterate_over_skills(df=set_df)
                self._merge_range(worksheet, set_start, 1, row-1, 1, s, frmts['merge'][merge_s%2], frmts['data'][merge_s%2])
                merge_s += 1
            # Write total
            total_start = row
            iterate_over_skills(df=df.groupby('skill', as_index=False)[symbols].sum())
            self._merge_range(worksheet, total_start, 1, row-1, 1, 'TOTAL', frmts['merge'][merge_s%2], frmts['data'][merge_s%2])
            merge_s += 1
            # Merge lead column
            worksheet.merge_range(team_start, 0, row-1, 0, name, frmts['merge'][merge_key%2])
            merge_key += 1
            row += 1

        if ws_team is None:
            def plot_attack_after_receive(ws: Worksheet, row: int, col: int, team: Teams, df: pd.DataFrame) -> None:
                attack_df = (
                    df[(df['skill'] == NmonSkill.ATTACK) & (df['skill'].shift(1) == NmonSkill.RECEIVE)]
                    .value_counts('num')
                )
                fig_pie.clear_axes()
                fig_pie.make_pie(attack_df.tolist(), [self.players[team].get(n, str(n)) for n in attack_df.index], ExcelReport.COLORS['players'][:len(attack_df.index)])
                fig_pie.set_title(f"Attack distribution after receive: {team.upper()}")
                self._insert_image(ws, row, col, fig_pie.save_bytes(), 0.9)
            
            # Plot attack after receive pie chart
            row = 1
            for team, team_df in data.items():
                team = cast(Teams, team)
                plot_attack_after_receive(worksheet, row, 18, team, team_df)
                row += 19
            # Plot errors and points bar chart
            counts: dict[Teams, dict[str, pd.Series[int]]] = {}
            for team, team_df in data.items():
                success_count = team_df[team_df['skill'].isin(skills_to_point) & team_df['#'].eq(1)].groupby('skill').size().reindex(skills_to_point, fill_value=0)
                error_count = team_df[team_df['skill'].isin(skills_to_error) & team_df['='].eq(1)].groupby('skill').size().reindex(skills_to_error, fill_value=0)
                counts[cast(Teams, team)] = {'points': success_count, 'errors': error_count}

            fig_bar.clear_axes()
            fig_bar.make_horizontal_bars(
                labels=['Home', 'Away'],
                groups=[
                    BarFigure.BarsGroup(
                        names=[f"{e.name} POINT" for e in counts['home']['points'].index],
                        values=np.array([counts['home']['points'], counts['away']['points']]),
                        colors=ExcelReport.COLORS['skill_point']
                    ),
                    BarFigure.BarsGroup(
                        names=[f"{e.name} ERROR" for e in counts['home']['errors'].index],
                        values=np.array([counts['home']['errors'], counts['away']['errors']]),
                        colors=ExcelReport.COLORS['skill_error']
                    )
                ],
                height=0.5,
                vspace=1.5
            )
            fig_bar.set_axes('horizontal_bars')
            fig_bar.set_title("Error comparison")
            self._insert_image(worksheet, row, 18, fig_bar.save_bytes())

        elif ws_team in ('home', 'away'):
            # Plot errors vs points per player bar chart
            num_counts: dict[Scalar, dict[str, pd.Series[int]]] = {}            
            for num, num_df in data.items():
                num_counts[num] = {
                    'points': num_df[num_df['skill'].isin(skills_to_point) & num_df['#'].eq(1)].groupby('skill').size().reindex(skills_to_point, fill_value=0),
                    'errors': num_df[num_df['skill'].isin(skills_to_error) & num_df['='].eq(1)].groupby('skill').size().reindex(skills_to_error, fill_value=0)
                }

            fig_bar.clear_axes()
            fig_bar.make_horizontal_bars(
                labels=[str(names.get(n, n)) for n in num_counts.keys()], #type: ignore
                groups=[
                    BarFigure.BarsGroup(
                        names=[f"{e.name} POINT" for e in num_counts[list(num_counts.keys())[0]]['points'].index],
                        values=np.array([v['points'] for v in num_counts.values()]),
                        colors=ExcelReport.COLORS['skill_point']
                    ),
                    BarFigure.BarsGroup(
                        names=[f"{e.name} ERROR" for e in num_counts[list(num_counts.keys())[0]]['errors'].index],
                        values=np.array([v['errors'] for v in num_counts.values()]),
                        colors=ExcelReport.COLORS['skill_error']
                    )
                ],
                height=0.5,
                vspace=2
            )
            fig_bar.set_axes('horizontal_bars')
            fig_bar.set_title('Error comparison')
            self._insert_image(worksheet, 1, 18, fig_bar.save_bytes())


    def build_worksheet_atack(self, ws_team: Teams) -> None:
        # Variables setup
        symbols = self._value_symbols
        frmt, frmts = self.formats, self.formats_list
        fig_court = CourtFigure()
        fig_pie = PieFigure()

        skill = NmonSkill.ATTACK
        columns = ["Player", "Hit", "Ext.", *self._eff_header]
        distribution: dict[int, set[NmonExt]] = {
            2: {NmonExt.X1, NmonExt.X2, NmonExt.X8, NmonExt.K9},
            3: {NmonExt.X3, NmonExt.X6, NmonExt.X9, NmonExt.K1, NmonExt.K2, NmonExt.K3, NmonExt.K4, NmonExt.K5, NmonExt.K6, NmonExt.K7, NmonExt.K8},
            4: {NmonExt.X4, NmonExt.X5, NmonExt.X7}
        } # ext classified by net side
        tip_ext = {NmonExt.X7, NmonExt.X8, NmonExt.K8} # ext considered as soft attacks
        # Worksheet setup
        ws_name = Sheet.HOME_ATTACK if ws_team=='home' else (Sheet.AWAY_ATTACK if ws_team=='away' else '') # CHECK 3RD CASE
        data: dict[Scalar, pd.DataFrame] = self.groups[ws_team]['num']
        names: dict[Any, str] = self.players[ws_team]
        worksheet = self._new_worksheet(ws_name)
        worksheet.set_column(0, 0, self._get_fit_width(list(names.values())))
        # Write worksheet
        row = 0
        for num, df in data.items():
            num_df = (
                df[df['skill']==skill]
                .groupby(['hit', 'ext', 'zone'], as_index=False)[symbols]
                .sum()
                .assign(count=lambda df: df[symbols].sum(axis=1))
            )
            if num_df.empty:
                continue

            name = names.get(num, num)
            self._write_header(worksheet, row, 0, columns, frmt['header'])
            worksheet.write(row, 18, "Emblems", frmt['header']) #INSIGNIAS
            row += 1
            # Write attack for each hit-ext
            num_start = row
            hit_df = num_df.groupby(['hit', 'ext'], sort=False, as_index=False)[symbols].sum()
            for hit, ext, *values in hit_df.itertuples(index=False, name=None):
                efficiency = self._get_efficiency(skill, pd.Series(values, index=symbols))
                worksheet.write_row(row, 1, [hit.name, ext.name, *efficiency], frmts['data'][row%2])
                row += 1
            # Write total for each num
            total_eff = self._get_efficiency(skill, num_df[symbols].sum())
            worksheet.merge_range(row, 1, row, 2, 'TOTAL', frmts['merge'][row%2])
            worksheet.write_row(row, 3, total_eff, frmts['data'][row%2])
            row += 2
            # Plot attack percent for each ext (pie chart)
            pie_df = (
                hit_df
                .assign(label=hit_df['ext'].mask(hit_df['ext']==NmonExt.NONE, hit_df['hit']))
                .groupby('label', sort=False)[symbols]
                .sum()
            )
            pie_sum = pie_df[symbols].sum(axis=1)
            if pie_sum.sum() <= ExcelReport.MIN_REPS['attack']:
                worksheet.merge_range(num_start, 0 , row-2, 0, name, frmts['merge'][num_start%2])
                continue
            fig_pie.clear_axes()
            fig_pie.make_pie_hit(pie_sum.tolist(), pie_df.index.tolist())
            fig_pie.set_title(f"Attack distribution player {name}")
            self._insert_image(worksheet, row, 1, fig_pie.save_bytes(), 0.9, (10, 0))

            # Plot attack direction percents
            net_col = 7
            for net, ext_tuple in distribution.items():
                ext_df = (
                    num_df[num_df['ext'].isin(ext_tuple)]
                    .groupby(['ext', 'zone'], as_index=False)
                    .agg(count=('count', 'sum'))
                    .assign(per=lambda df: df['count'] / df['count'].sum())
                )
                count_attack_err = (
                    num_df[num_df['ext'].isin(ext_tuple - tip_ext)]
                    .groupby(['ext', 'zone'], as_index=False)
                    .agg(count=('count', 'sum'), err_count=('=', 'sum'))
                    .assign(
                        per=lambda df: df['count'] / df['count'].sum(),
                        err_per=lambda df: df['err_count'] / df['count'].sum()
                    )
                )
                if ext_df.empty or ext_df['count'].sum() <= ExcelReport.MIN_REPS['attack_distribution']:
                    continue

                ext_counts = ext_df.groupby('ext')['count'].sum()
                min_reps_defender = ExcelReport.MIN_REPS['attack_defender']
                if ext_counts.get(NmonExt.X1, 0) > min_reps_defender or ext_counts.get(NmonExt.X6, 0) > min_reps_defender:
                    title = f"Attacks by {name} from {net} --- DEFENDER ATTACK PRIORITY"
                    # fig_court.figure.patch.set_facecolor(ExcelReport.COLORS['court_bg'][0])
                    highlight = True
                else:
                    title = f"Attacks by {name} from {net}"
                    # fig_court.figure.patch.set_facecolor(ExcelReport.COLORS['court_bg'][1])
                    highlight = False

                fig_court.clear_axes()
                # Plot attack vs soft attacks (middle)
                tip_percent = ext_df[ext_df['ext'].isin(tip_ext)]['per'].sum()
                err_percent = count_attack_err['err_per'].sum()
                fig_court.print_attack_vs_tip((1-tip_percent, 1-err_percent, err_percent), tip_percent)
                # Plot arrows to attack zones (left court)
                zone_percents = ext_df.groupby('zone')['per'].sum()
                for zone, per in zone_percents.items():
                    fig_court.create_arrow(net, NmonZone(zone), per)
                # Plot type of attack (right court)
                for d in ext_df[['ext', 'zone', 'count']].itertuples(index=False, name=None):
                    fig_court.create_scatter(NmonHit.HIGH, *d)
                fig_court.create_legends()
                fig_court.set_title(title, highlight)
                self._insert_image(worksheet, row, net_col, fig_court.save_bytes(), 0.85)
                net_col += 13
            row += 15

            worksheet.merge_range(num_start, 0 , row, 0, name, frmts['merge'][num_start%2])
            row += 2
    

    def build_worksheet_serve(self, ws_team: Teams) -> None:
        # Variables setup
        symbols = self._value_symbols
        frmt, frmts = self.formats, self.formats_list
        fig_pie = PieFigure()
        
        skill = NmonSkill.SERVE
        columns = ["Player", "Hit", "Ext.", *self._eff_header]
        # Worksheet setup
        ws_name = Sheet.HOME_SERVE if ws_team=='home' else (Sheet.AWAY_SERVE if ws_team=='away' else "") # CHECK 3RD CASE
        data: dict[Scalar, pd.DataFrame] = self.groups[ws_team]['num']
        names: dict[Any, str] = self.players[ws_team]
        worksheet = self._new_worksheet(ws_name)
        worksheet.set_column(0, 0, self._get_fit_width(list(names.values())))
        # Write worksheet
        row = 0
        for num, df in data.items():
            num_df = df[df['skill']==skill].groupby(['hit', 'ext'], as_index=False)[symbols].sum()
            if num_df.empty:
                continue

            name = names.get(num, num)
            self._write_header(worksheet, row, 0, columns, frmt['header'])
            worksheet.write(row, 18, "Emblems", frmt['header']) #INSIGNIAS
            row += 1

            num_start = row
            hit_values: dict[NmonHit, list[int]] = {}
            for hit, ext, *values in num_df.itertuples(index=False, name=None):
                hit_values[hit] = list(values)
                efficiency = self._get_efficiency(skill, pd.Series(values, index=symbols))
                worksheet.write_row(row, 1, [hit.name, ext.name, *efficiency], frmts['data'][row%2])
                row += 1
            
            total_serve = num_df[symbols].sum()
            total_eff = self._get_efficiency(skill, total_serve)
            worksheet.merge_range(row, 1, row, 2, 'TOTAL', frmts['merge'][row%2])
            worksheet.write_row(row, 3, total_eff, frmts['data'][row%2])
            row += 2
            # Plot a pie chart for total serves
            if total_serve.sum() <= ExcelReport.MIN_REPS['serve']:
                worksheet.merge_range(num_start, 0, row-2, 0, name, frmts['merge'][num_start%2])
                continue
            pie_col = 1
            fig_pie.clear_axes()
            fig_pie.make_pie(total_serve.tolist(), symbols, ExcelReport.COLORS['symbols'])
            fig_pie.set_title(f"TOTAL serves: {name}")
            self._insert_image(worksheet, row, pie_col, fig_pie.save_bytes(), 0.9, (10, 0))
            pie_col += 6
            # Plot pie chart for each type of serve
            if len(hit_values) > 1:
                for hit, values in hit_values.items():
                    if sum(values) <= ExcelReport.MIN_REPS['serve_hit']:
                        continue
                    fig_pie.clear_axes()
                    fig_pie.make_pie(values, symbols, ExcelReport.COLORS['symbols'])
                    fig_pie.set_title(f"{hit.name} serves: {name}")
                    self._insert_image(worksheet, row, pie_col, fig_pie.save_bytes(), 0.9, (10, 0))
                    pie_col += 6
            row += 15

            worksheet.merge_range(num_start, 0, row, 0, name, frmts['merge'][num_start%2])
            row += 2
        

    def build_worksheet_receive(self, ws_team: Teams) -> None:
        # Variables setup
        symbols = self._value_symbols
        frmt, frmts = self.formats, self.formats_list
        fig_pie = PieFigure()
        fig_bar = BarFigure()

        if ws_team == 'home':
            ws_name = Sheet.HOME_RECEIVE
            names_enemy: dict[Any, str] = self.players['away']
        elif ws_team == 'away':
            ws_name = Sheet.AWAY_RECEIVE
            names_enemy: dict[Any, str] = self.players['home']
        else:
            raise ValueError(f"ws_name must be Sheet.{Sheet.HOME_RECEIVE} or Sheet.{Sheet.AWAY_RECEIVE}")
        data: pd.DataFrame = self.groups[ws_team]['receive']
        names: dict[Any, str] = self.players[ws_team]

        skill = NmonSkill.RECEIVE
        columns = ["Player", "Rotation", "Hit", *self._eff_header]
        rotation = 'home_rot' if ws_name == Sheet.HOME_RECEIVE else 'away_rot'
        # Worksheet setup
        worksheet = self._new_worksheet(ws_name)
        worksheet.set_column(0, 0, self._get_fit_width(list(names.values())))

        data.loc[data['skill']==skill, 'serve'] = data['num'].shift(1).astype('Int64')
        data = data[data['skill']==skill].reset_index()

        row, merge_rot = 0, 0
        for num, df in data.groupby('num', as_index=False):
            num_df = (
                df[df['skill']==NmonSkill.RECEIVE]
                .groupby([rotation, 'hit', 'zone'], as_index=False)[symbols]
                .sum()
            )
            if num_df.empty:
                continue

            name = names.get(num, num)
            self._write_header(worksheet, row, 0, columns, frmt['header'])
            worksheet.write(row, 18, "Emblems", frmt['header']) #INSIGNIAS
            row += 1

            num_start = row
            for rot, rot_df in num_df.groupby(rotation, sort=False, as_index=False):
                rotation_start = row
                for _, hit, _, *values in rot_df.itertuples(index=False, name=None):
                    efficiency = self._get_efficiency(skill, pd.Series(values, index=symbols))
                    worksheet.write_row(row, 2, [hit.name, *efficiency], frmts['data'][row%2])
                    row += 1
                
                total_rot = self._get_efficiency(skill, rot_df[symbols].sum())
                worksheet.write_row(row, 2, ['TOTAL', *total_rot], frmts['data'][row%2])

                worksheet.merge_range(rotation_start, 1, row, 1, rot, frmts['merge'][merge_rot%2])
                merge_rot += 1
                row += 1
            
            total_start = row
            total_hit: dict[NmonHit, pd.Series[Any]] = {}
            for hit, hit_df in num_df.groupby('hit', sort=False, as_index=False):
                sum_hit = hit_df[symbols].sum()
                efficiency = self._get_efficiency(skill, sum_hit)
                worksheet.write_row(row, 2, [hit.name, *efficiency], frmts['data'][row%2]) #type: ignore
                total_hit[NmonHit(hit)] = sum_hit
                row += 1

            total_receive = num_df[symbols].sum()
            total_eff = self._get_efficiency(skill, total_receive)
            worksheet.write_row(row, 2, ['TOTAL', *total_eff], frmts['data'][row%2])
            worksheet.merge_range(total_start, 1, row, 1, 'TOTAL', frmts['merge'][merge_rot%2])
            row += 2

            if total_receive.sum() <= ExcelReport.MIN_REPS['receive']:
                worksheet.merge_range(num_start, 0, row-2, 0, name, frmts['merge'][num_start%2])
                continue

            fig_pie.clear_axes()
            fig_pie.make_pie(total_receive.tolist(), symbols, ExcelReport.COLORS['symbols'])
            fig_pie.set_title(f"Receive values player {name}")
            self._insert_image(worksheet, row, 1, fig_pie.save_bytes(), 0.9, (10, 0))
            # row += 18
        
            col = 7
            for hit, values in total_hit.items():
                if values.sum() <= ExcelReport.MIN_REPS['receive_serve']:
                    continue
                fig_pie.clear_axes()
                fig_pie.make_pie(values.tolist(), symbols, ExcelReport.COLORS['symbols'])
                fig_pie.set_title(f"Receive values {hit.name} by player {name}")
                self._insert_image(worksheet, row, col, fig_pie.save_bytes(), 0.9)
                col += 6

            serve_df = data[data['num']==num].groupby('serve')[symbols].sum()
            fig_bar.clear_axes()
            fig_bar.make_vertical_bars(
                labels=[names_enemy.get(k, k) for k in serve_df.index], #type: ignore
                groups=[
                    BarFigure.BarsGroup(
                        names=serve_df.columns.tolist(),
                        values=serve_df.to_numpy(),
                        colors=ExcelReport.COLORS['symbols']
                    )
                ],
                width=0.5,
                hspace=2
            )
            fig_bar.set_axes('vertical_bars')
            fig_bar.set_title(f"Valoración recepción de {name} para cada sacador rival")
            self._insert_image(worksheet, row, col+1, fig_bar.save_bytes(), 0.8)
            row += 21

            col = 1
            for zone, zone_df in num_df.groupby('zone', sort=False, as_index=False)[symbols]:
                zone_values = zone_df.sum()
                if zone_values.sum() <= ExcelReport.MIN_REPS['receive_zone']:
                    continue
                fig_pie.clear_axes()
                fig_pie.make_pie(zone_values.tolist(), symbols, ExcelReport.COLORS['symbols'])
                fig_pie.set_title(f"Receve in {NmonZone(zone).name} by player {name}")
                self._insert_image(worksheet, row, col, fig_pie.save_bytes(), 0.9, (10, 0))
                col += 5
            if col > 1:
                row += 15

            worksheet.merge_range(num_start, 0, row, 0, name, frmts['merge'][num_start%2])
            row += 2
        

    def build_worksheet_objetives(self) -> None:
        worksheet = self._new_worksheet(Sheet.OBJETIVES)
        succeed = self.workbook.add_format({'bg_color': ExcelReport.COLORS['point']})
        fail = self.workbook.add_format({'bg_color': ExcelReport.COLORS['error']})
        
        worksheet.write_string(0, 0, 'Objetivos logrados', succeed)
        worksheet.write_formula(1, 0, '=COUNTIFS(A4:A100, "<>", B4:B100, "<>")')
        worksheet.set_column(0, 0, self._get_fit_width(['Objetivos logrados']))

        worksheet.write_string(0, 3, 'Objetivos incompletos', fail)
        worksheet.write_formula(1, 3, '=COUNTIFS(A4:A100, "", B4:B100, "<>")')
        worksheet.set_column(3, 3, self._get_fit_width(['Objetivos incompletos']))

        worksheet.write_row(2, 0, ['Marks', 'Objetives'])
        


    def _get_efficiency(self, skill: NmonSkill, values: pd.Series[int]) -> list[Scalar]:
        total = values.sum()
        eff = round(ExcelReport.EFF_FORMULA[skill](values, total) * 100, 1)
        value_abs_per = ((v, round(v / total * 100, 1)) for v in values) # (absolute value, percent value)
        # eff = self.EFF_FORMULA[skill](values, total)
        # value_abs_per = ((v, v / total) for v in values) # (absolute value, percent value)
        value_abs_per = ['' if v==0 else v for v in [x for y in value_abs_per for x in y]]
        return [total, eff, *value_abs_per]


    def _merge_range(
            self,
            ws: Worksheet,
            first_row: int,
            first_col: int,
            last_row: int,
            last_col: int,
            data: Any,
            merge_format: Optional[Format]=None,
            write_format: Optional[Format]=None
        ) -> None:
        if last_row == first_row and last_col == first_col:
            ws.write(first_row, first_col, data, write_format)
        else:
            ws.merge_range(first_row, first_col, last_row, last_col, data, merge_format)

    

    def _insert_image(self, ws: Worksheet, row: int, col: int, img_bytes: BytesIO, scale: float=1, offset: tuple[int,int]=(0,0)) -> None:
        img_bytes.seek(0)
        ws.insert_image(
            row=row,
            col=col,
            source=img_bytes,
            options={
                'x_scale': scale, 'y_scale': scale,
                'x_offset': offset[0], 'y_offset': offset[1]
            }
        )
    

    def export_raw(self) -> None:
        ws = self.workbook.add_worksheet('Raw data')
        ws.write_row(
            0,
            0,
            ['set', 'team', 'num', 'skill', 'hit', 'value', 'ext', 'zone', 'home_rot', 'away_rot'],
            self.formats['header']
        )
        for idx, g, t, n, s, h, v, e, z, hr, ar in self.df.itertuples(name=None):
            row = idx + 1
            ws.write_row(
                row,
                0,
                [g, t, n, s.name, NmonHit(h).name, v, e, z, hr, ar],
                self.formats_list['data'][row%2]
            )
            ws.write_string(row, 5, v, self.formats_list['data'][row%2])
    

    def _get_fit_width(self, data: list[Any]) -> int:
        min_width = 8
        return max(max(len(str(d)) for d in data), min_width) if data else min_width