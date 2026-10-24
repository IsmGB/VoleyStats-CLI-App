import xlsxwriter as xlsx
import logging
import numpy as np
from pathlib import Path
from pandas import DataFrame
from enum import IntEnum
from typing import Self

from voleystats.analysis.data_analyst import *
from voleystats.analysis.validation import Team
from voleystats.analysis.excel_sheets import *
from voleystats.enums import TeamKey
# from voleystats.analysis.graphs import BarFigure, CourtFigure, PieFigure
from voleystats.analysis.sheet_mapper import *
from voleystats.colors import *
from voleystats.graphs import *


logger = logging.getLogger(__name__)


class MinReps(IntEnum):
    ATTACK = 2
    ATTACK_DISTRIBUTION = 2
    ATTACK_DEFENDER = 2
    SERVE = 2
    SERVE_HIT = 2
    RECEIVE = 2
    RECEIVE_SERVE = 2
    RECEIVE_ZONE = 2



class ExcelReport:
    def __init__(self, excelfile: Path, dataframe: DataFrame, teams: dict[TeamKey, Team]) -> None:
        self.excelfile = excelfile
        self.core = CoreData(df=dataframe)

        self.sheets: list[Sheet] = []
        self.names = {
            k: {n: item.get(n, str(n)) for n in self.core.get_numbers(k)}
            for k, team in teams.items() for item in (team.asdict(),)
        }

    def __enter__(self) -> Self:
        self.workbook = xlsx.Workbook(self.excelfile)
        self.formats = SheetFormats(self.workbook)
        return self
    
    def __exit__(self, exc_type, exc, tb):
        self.workbook.close()
    

    def build_sheet_main(self) -> None:
        home = self.core.teams['home']
        away = self.core.teams['away']

        home_points = TeamsAnalyst.get_points_count(home)
        home_errors = TeamsAnalyst.get_errors_count(home)
        away_points = TeamsAnalyst.get_points_count(away)
        away_errors = TeamsAnalyst.get_errors_count(away)

        fig = HBarFigure()
        fig.make_bars(
            labels=['Home', 'Away'],
            groups=[
                BarsGroup(
                    names=[f"{e.name} POINT" for e in home_points.index],
                    values=np.array([home_points, away_points]),
                    colors=[c.value for c in ColorPoint][:3]
                ),
                BarsGroup(
                    names=[f"{e.name} ERROR" for e in home_errors.index],
                    values=np.array([home_errors, away_errors]),
                    colors=[c.value for c in ColorError][:6]
                )
            ],
            width=0.5,
            space=1.5
        )
        fig.set_axes()
        fig.set_title("Comparación de puntos y errores")

        cnt = Container(
            data={
                'home': Container(
                    data={
                        'name': 'Home',
                        'eff': TeamMapper.map_efficiency(TeamsAnalyst.get_efficiency(home)),
                        'total': TeamMapper.map_total_efficiency(TeamsAnalyst.get_total_efficiency(home))
                    }
                ),
                'away': Container(
                    data={
                        'name': 'Away',
                        'eff': TeamMapper.map_efficiency(TeamsAnalyst.get_efficiency(away)),
                        'total': TeamMapper.map_total_efficiency(TeamsAnalyst.get_total_efficiency(away))
                    }
                )
            },
            charts={'pts': fig.save_bytes()}
        )

        self.sheets.append(
            MainSheet(
                name='MAIN',
                workbook=self.workbook,
                contents=cnt,
                formats=self.formats
            )
        )
    

    def build_sheet_team(self, team: TeamKey) -> None:
        players = self.core.players[team]
        nums = self.core.get_numbers(team)
        names = self.names[team]


        points, errors = {}, {}
        for n,ply in players.items():
            points[n] = TeamsAnalyst.get_points_count(ply)
            errors[n] = TeamsAnalyst.get_errors_count(ply)

        fig = HBarFigure()
        fig.make_bars(
            labels=list(names.values()),
            groups=[
                BarsGroup(
                    names=[f"{e.name} POINT" for e in points[nums[0]].index],
                    values=np.array(list(points.values())),
                    colors=[c.value for c in ColorPoint][:3]
                ),
                BarsGroup(
                    names=[f"{e.name} ERROR" for e in errors[nums[0]].index],
                    values=np.array(list(errors.values())),
                    colors=[c.value for c in ColorError][:6]
                )
            ],
            width=0.5,
            space=1.5
        )
        fig.set_axes()
        fig.set_title("Comparación de puntos y errores")

        cnt = Container(
            data={
                n: Container(
                    data={
                        'name': names[n],
                        'eff': TeamMapper.map_efficiency(TeamsAnalyst.get_efficiency(ply)),
                        'total': TeamMapper.map_total_efficiency(TeamsAnalyst.get_total_efficiency(ply))
                    }
                ) for n, ply in players.items()
            },
            charts={'pts': fig.save_bytes()}
        )

        self.sheets.append(
            TeamsSheet(
                name=team.upper(),
                workbook=self.workbook,
                contents=cnt,
                formats=self.formats
            )
        )


    def build_sheet_attack(self, team: TeamKey) -> None:
        tips = ExtEnum.get_tips()
        attacks = ExtEnum.get_distribution()
        names = self.names[team]

        pie = PieFigure()
        court = CourtFigure()

        cnt_data: dict[int, Container] = {}
        for n,grp in self.core.players[team].items():
            if (ply := BasicAnalyst.filter_by_skill(grp, SkillEnum.ATTACK)).empty:
                continue
            name = names[n]
            cnt_data[n] = Container(
                data = {
                    'name': name,
                    'eff': AttackMapper.map_efficiency(AttackAnalyst.get_efficiency(ply)),
                    'total': AttackMapper.map_total_efficiency(AttackAnalyst.get_total_efficiency(ply))
                }
            )

            pie_total = AttackAnalyst.get_ext_totals(ply)
            if pie_total.sum() <= MinReps.ATTACK:
                continue
            pie.clear_axes()
            labels = pie_total.index.to_list()
            pie.make_pie(
                values=pie_total.to_list(),
                labels=labels,
                colors=[COLORS_HIT_EXT[lbl.name] for lbl in labels]
            )
            pie.set_title(f"Ataques de {name}")

            chart_net: list[BytesIO] = []
            for net, ext in attacks.items():
                atk_tip_df = AttackAnalyst.get_ext_count(ply, ext)
                if atk_tip_df.empty or atk_tip_df['count'].sum() <= MinReps.ATTACK_DISTRIBUTION:
                    continue

                ext_counts = atk_tip_df.groupby('ext')['count'].sum()
                if ext_counts.get(ExtEnum.X1, 0) > MinReps.ATTACK_DEFENDER or ext_counts.get(ExtEnum.X6, 0) > MinReps.ATTACK_DEFENDER:
                    title = f"Distribución de ataque de {name} por red {net}" + ": PRIORIDAD ZAGUERO"
                    highlight = True
                else:
                    title = f"Distribución de ataque de {name} por red {net}"
                    highlight = False
            
                tip_percent = AttackAnalyst.get_tip_percent(ply, net)
                err_percent = AttackAnalyst.get_error_percent(ply, net)

                court.clear_axes()
                court.print_attack_pertents(1-tip_percent, 1-err_percent, err_percent, tip_percent)
                zone_percent = atk_tip_df.groupby('zone')['per'].sum()
                for zone, per in zone_percent.items():
                    court.create_arrow(net, ZoneEnum(zone), per)
                for d in atk_tip_df[['ext', 'zone', 'count']].itertuples(index=False, name=None):
                    court.create_scatter(HitEnum.HIGH, *d)
                court.set_title(title, highlight)
                chart_net.append(court.save_bytes())
            cnt_data[n].charts = {'pie': pie.save_bytes(), 'courts': chart_net}

        self.sheets.append(
            AttackSheet(
                name=f"ATQ - {team.upper()}",
                workbook=self.workbook,
                contents=Container(data=cnt_data),
                formats=self.formats
            )
        )


    def build_sheet_serve(self, team: TeamKey) -> None:
        names = self.names[team]

        fig = PieFigure()

        cnt_data: dict[int, Container] = {}
        for n,grp in self.core.players[team].items():
            if (ply := BasicAnalyst.filter_by_skill(grp, SkillEnum.SERVE)).empty:
                continue
            name = names[n]
            cnt_data[n] = Container(
                data = {
                    'name': name,
                    'eff': ServeMapper.map_efficiency(ServeAnalyst.get_efficiency(ply)),
                    'total': ServeMapper.map_total_efficiency(ServeAnalyst.get_total_efficiency(ply))
                }
            )

            serve_values = BasicAnalyst.get_values_count(ply)
            if serve_values.sum() <= MinReps.SERVE:
                continue
            fig.clear_axes()
            fig.make_pie(serve_values.to_list(), SYMBOLS, list(ColorValue))
            fig.set_title(f"Valoración total de saques: {name}")
            pie_bytes = fig.save_bytes()

            pies: list[BytesIO] = []
            if len(df := ServeAnalyst.get_values_per_hit(ply)) > 1:
                for hit, *values in df.itertuples(index=False, name=None):
                    if sum(values) <= MinReps.SERVE_HIT:
                        continue
                    fig.clear_axes()
                    fig.make_pie(values, SYMBOLS, list(ColorValue))
                    fig.set_title(f"Valoración de saque {hit.name}: {name}")
                    pies.append(fig.save_bytes())
            cnt_data[n].charts = {'pie': pie_bytes, 'hit_pies': pies}
        
        self.sheets.append(
            ServeSheet(
                workbook=self.workbook,
                name=f"SAQ. - {team.upper()}",
                contents=Container(data=cnt_data),
                formats=self.formats
            )
        )


    def build_sheet_receive(self, team: TeamKey) -> None:
        names = self.names[team]

        df = ReceiveAnalist.get_serve_receive(self.core.df, team)
        df = ReceiveAnalist.keep_rotation(df, team)

        pie = PieFigure()
        bar = VBarFigure()

        cnt_data: dict[int, Container] = {}
        for n, ply in BasicAnalyst.get_players(df).items():
            name = names[n]
            data = {
                'name': name,
                'eff': ReceiveMapper.map_efficiency(ReceiveAnalist.get_efficiency(ply)),
                'total': ReceiveMapper.map_total_efficiency(ReceiveAnalist.get_total_efficiency(ply))
            }
            cnt_data[n] = Container(data=data)

            receive_values = BasicAnalyst.get_values_count(ply)
            if receive_values.sum() <= MinReps.RECEIVE:
                continue
            # VALORACIÓN TOTAL DE RECE
            pie.clear_axes()
            pie.make_pie(receive_values.to_list(), SYMBOLS, list(ColorValue))
            pie.set_title(f"Valoración total de recepción: {name}")
            pie_bytes = pie.save_bytes()
            # VALORACIÓN POR TIPO DE SAQUE
            pies: list[BytesIO] = []
            for hit, item in data['eff'].items():
                values = item['total']
                if sum(values[2::2]) <= MinReps.RECEIVE_SERVE:#hacer suma sobre symbols, no sobre eff!!
                    continue
                pie.clear_axes()
                pie.make_pie(values[2::2], SYMBOLS, list(ColorValue))
                pie.set_title(f"Valoración de recepción tipo {hit.name}: {name}")
                pies.append(pie.save_bytes())
            # VALORACIÓN POR SACADOR
            serve_df = ReceiveAnalist.group_by_serve(ply)
            labels = self.names['away' if team == 'home' else 'home']
            bar.make_bars(
                labels=[labels[n] for n in serve_df.index if n in labels],
                groups=[
                    BarsGroup(
                        names=serve_df.columns.to_list(),
                        values=serve_df.to_numpy(),
                        colors=list(ColorValue)
                    )
                ],
                width=0.5, space=2
            )
            bar.set_axes()
            bar.set_title(f"Valoración de recepción por sacador rival: {name}")
            # VALORACIÓN POR ZONA EN EL CAMPO
            zones: list[BytesIO] = []
            for zone, *values in ReceiveAnalist.group_by_zone(ply).itertuples(index=False, name=None):
                if sum(values) <= MinReps.RECEIVE_ZONE:
                    continue
                pie.clear_axes()
                pie.make_pie(values, SYMBOLS, list(ColorValue))
                pie.set_title(f"Valoración de recepción en zona {zone}: {name}")
                zones.append(pie.save_bytes())
            cnt_data[n].charts = {'pie': pie_bytes, 'rot_pies': pies, 'bar': bar.save_bytes(), 'zones': zones}
            
        self.sheets.append(
            ReceiveSheet(
                name=f"RECV. - {team.upper()}",
                workbook=self.workbook,
                contents=Container(data=cnt_data),
                formats=self.formats
            )
        )