from io import BytesIO
from pathlib import Path

import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import LineCollection, PathCollection
from matplotlib.patches import FancyArrowPatch, ArrowStyle
from matplotlib.text import Text
from matplotlib.lines import Line2D
from typing import Any

from voleystats.enums import *
from voleystats.colors import ColorsHit, ColorsExt, Colors
from .base_figure import BaseFigure


type PathCollectionDuo = tuple[PathCollection, PathCollection]


class ArrowColors(StrEnum):
    A1 = "#0072B2"
    A2 = "#E69F00"
    A3 = "#009E73"
    A4 = "#5911B8"
    A5 = "#E26607"
    A6 = "#56B4E9"
    A7 = "#6B8E23"
    A8 = "#8C564B"
    A9 = "#C2185B"



class CourtFigure(BaseFigure):
    _BOUNDARIES = [
            {'line': [(0.2, 0.8), (0.2, 0.2)], 'lw': 2, 'ls': 'solid'}, # left
            {'line': [(0.2, 0.2), (0.8, 0.2)], 'lw': 2, 'ls': 'solid'}, # bottom
            {'line': [(0.8, 0.2), (0.8, 0.8)], 'lw': 2, 'ls': 'solid'}, # right
            {'line': [(0.2, 0.6), (0.8, 0.6)], 'lw': 2, 'ls': 'solid'}, # defense
            {'line': [(0.1, 0.8), (0.9, 0.8)], 'lw': 4, 'ls': 'solid'}, # net
            {'line': [(0.13, 0.6), (0.87, 0.6)], 'lw': 1.5, 'ls': 'dashed'}, # defense dashed
            {'line': [(0.2, 0.185), (0.2, 0.17)], 'lw': 2, 'ls': 'solid'}, # left serve dot
            {'line': [(0.8, 0.185), (0.8, 0.17)], 'lw': 2, 'ls': 'solid'}, # right serve dot
        ]
    _GRID = [
            [(0.4, 0.8), (0.4, 0.2)], # separator 5-6
            [(0.6, 0.8), (0.6, 0.2)], # separator 6-1
            [(0.2, 0.4), (0.8, 0.4)], # separator defense
        ]
    _ARROW_STARTS = {
        2: (0.28, 0.85),
        3: (0.5, 0.85),
        4: (0.72, 0.85)
    }
    _ARROW_ENDS = {
        ZoneEnum.Z1: (0.7, 0.3),
        ZoneEnum.Z2: (0.7, 0.7),
        ZoneEnum.Z3: (0.5, 0.7),
        ZoneEnum.Z4: (0.3, 0.7),
        ZoneEnum.Z5: (0.3, 0.3),
        ZoneEnum.Z6: (0.5, 0.3),
        ZoneEnum.Z7: (0.3, 0.5),
        ZoneEnum.Z8: (0.5, 0.5),
        ZoneEnum.Z9: (0.7, 0.5)
    }
    _ARROW_COLORS = {zone: clr for zone, clr in zip(ZoneEnum, ArrowColors)}
    _ARROW_LBL_XY = {
        ZoneEnum.Z1: (0.7, 0.21),
        ZoneEnum.Z2: (0.7, 0.61),
        ZoneEnum.Z3: (0.5, 0.61),
        ZoneEnum.Z4: (0.3, 0.61),
        ZoneEnum.Z5: (0.3, 0.21),
        ZoneEnum.Z6: (0.5, 0.21),
        ZoneEnum.Z7: (0.3, 0.41),
        ZoneEnum.Z8: (0.5, 0.41),
        ZoneEnum.Z9: (0.7, 0.41)
    }
    _MIN_TIPS = 0.35
    _ZONE_CORNERS = ((0.22, 0.38), (0.42, 0.58), (0.62, 0.78))
    _ZONE_SQUARES = {
        ZoneEnum.Z1: (_ZONE_CORNERS[2], _ZONE_CORNERS[0]), # ((xmin, xmax), (ymin, ymax))
        ZoneEnum.Z2: (_ZONE_CORNERS[2], _ZONE_CORNERS[2]),
        ZoneEnum.Z3: (_ZONE_CORNERS[1], _ZONE_CORNERS[2]),
        ZoneEnum.Z4: (_ZONE_CORNERS[0], _ZONE_CORNERS[2]),
        ZoneEnum.Z5: (_ZONE_CORNERS[0], _ZONE_CORNERS[0]),
        ZoneEnum.Z6: (_ZONE_CORNERS[1], _ZONE_CORNERS[0]),
        ZoneEnum.Z7: (_ZONE_CORNERS[0], _ZONE_CORNERS[1]),
        ZoneEnum.Z8: (_ZONE_CORNERS[1], _ZONE_CORNERS[1]),
        ZoneEnum.Z9: (_ZONE_CORNERS[2], _ZONE_CORNERS[1])
    }
    _MRK_STYLES = {
        HitEnum.HIGH: {'marker': '$H$', 'color': ColorsHit.HIGH, 'markersize': 6},
        HitEnum.MEDIUM: {'marker': '$M$', 'color': ColorsHit.MEDIUM, 'markersize': 6},
        HitEnum.FAST: {'marker': '$N$', 'color': ColorsHit.FAST, 'markersize': 6},
        HitEnum.OTHER: {'marker': '$O$', 'color': ColorsHit.OTHER, 'markersize': 6},
        HitEnum.QUICK: {'marker': '$Q$', 'color': ColorsHit.QUICK, 'markersize': 6},
        HitEnum.TENSE: {'marker': '$T$', 'color': ColorsHit.TENSE, 'markersize': 6},
        HitEnum.SUPER: {'marker': '$U$', 'color': ColorsHit.SUPER, 'markersize': 6},
        ExtEnum.X1: {'marker': 'v', 'color': ColorsExt.X1, 'markersize': 6},
        ExtEnum.X2: {'marker': 'P', 'color': ColorsExt.X2, 'markersize': 6},
        ExtEnum.X3: {'marker': 's', 'color': ColorsExt.X3, 'markersize': 6},
        ExtEnum.X4: {'marker': 'o', 'color': ColorsExt.X4, 'markersize': 6},
        ExtEnum.X5: {'marker': 'X', 'color': ColorsExt.X5, 'markersize': 6},
        ExtEnum.X6: {'marker': '^', 'color': ColorsExt.X6, 'markersize': 6},
        ExtEnum.X7: {'marker': 'D', 'color': ColorsExt.X7, 'markersize': 6},
        ExtEnum.X8: {'marker': 'd', 'color': ColorsExt.X8, 'markersize': 6},
        ExtEnum.X9: {'marker': '*', 'color': ColorsExt.X9, 'markersize': 8},
        ExtEnum.K1: {'marker': 'X', 'color': ColorsExt.K1, 'markersize': 6},
        ExtEnum.K2: {'marker': 'P', 'color': ColorsExt.K2, 'markersize': 6},
        ExtEnum.K3: {'marker': 'v', 'color': ColorsExt.K3, 'markersize': 6},
        ExtEnum.K4: {'marker': 'o', 'color': ColorsExt.K4, 'markersize': 6},
        ExtEnum.K5: {'marker': '^', 'color': ColorsExt.K5, 'markersize': 6},
        ExtEnum.K6: {'marker': '<', 'color': ColorsExt.K6, 'markersize': 6},
        ExtEnum.K7: {'marker': 'd', 'color': ColorsExt.K7, 'markersize': 6},
        ExtEnum.K8: {'marker': 'D', 'color': ColorsExt.K8, 'markersize': 6},
        ExtEnum.K9: {'marker': '>', 'color': ColorsExt.K9, 'markersize': 6},
    }

    def __init__(self) -> None:
        LEFT, TOP, RIGHT, BOTTOM = 0.02, 0.12, 0.12, 0
        width = 1 - LEFT - RIGHT
        height = 1 - TOP - BOTTOM
        w1, w2, = width * 0.4, width * 0.2
        FIG_H = 4
        fig_w = 4 * (height / (0.4 * width))

        super().__init__(figsize=(fig_w, FIG_H))

        self.ax_arrows = self.add_axes((LEFT, BOTTOM, w1, height))
        self.ax_nums = self.add_axes((LEFT+w1, BOTTOM, w2, height))
        self.ax_scatter = self.add_axes((LEFT+w1+w2, BOTTOM, w1, height))

        self._set_axes()
        self._draw_court(self.ax_arrows)
        self._draw_court(self.ax_scatter)

        self._arrows: list[FancyArrowPatch] = list()
        self._arrow_lbls: list[Text] = list()
        self._nums: list[Text] = list()
        self._scatters: list[PathCollection|PathCollectionDuo] = list()
        self._legends: set[HitEnum|ExtEnum] = set()
        self._counts: dict[HitEnum|ExtEnum, int] = dict()

    
    def _set_axes(self) -> None:
        self.ax_arrows.set_xlim(0, 1)
        self.ax_arrows.set_ylim(0, 1)
        self.ax_arrows.axis('off')

        self.ax_scatter.set_xlim(0, 1)
        self.ax_scatter.set_ylim(0, 1)
        self.ax_scatter.axis('off')

        self.ax_nums.set_xlim(0, 1.2)
        self.ax_nums.set_ylim(0, 1)
        self.ax_nums.axis('off')
    

    def _draw_court(self, ax: Axes) -> None:
        segments, linewidths, linestyles = [], [], []
        for item in self._BOUNDARIES:
            segments.append(item['line'])
            linewidths.append(item['lw'])
            linestyles.append(item['ls'])
        ax.add_collection(
            LineCollection(
                segments=segments,
                colors=Colors.BLACK,
                linewidths=linewidths,
                linestyles=linestyles,
                zorder=0
            )
        )
        ax.add_collection(
            LineCollection(
                segments=self._GRID,
                colors=Colors.LIGHT_GREY,
                linewidths=0.6,
                linestyles='dashed',
                zorder=0
            )
        )
    

    def create_arrow(self, net: int, zone: ZoneEnum, percent: float) -> None:
        arrow = FancyArrowPatch(
            posA=self._ARROW_STARTS.get(net),
            posB=self._ARROW_ENDS[zone],
            arrowstyle=ArrowStyle(
                stylename="Simple",
                head_length=1.2,
                head_width=1.2,
                tail_width=0.5
            ),
            mutation_scale=25 if percent > 0.5 else (15 if percent > 0.2 else 10),
            color=self._ARROW_COLORS[zone],
            zorder=(1-percent) * 100
        )

        self.ax_arrows.add_patch(arrow)
        self._arrows.append(arrow)

        self._arrow_lbls.append(
            self.ax_arrows.text(
                *self._ARROW_LBL_XY[zone],
                s=f"{percent*100:.1f}%",
                fontweight='bold',
                ha='center',
                va='baseline',
                zorder=100
            )
        )
    

    def print_attack_pertents(self, total: float, good: float, error: float, tips: float) -> None:
        CONFIG: dict[str, Any] = {'weight': 'bold', 'ha': 'center'}
        self._nums.append(self.ax_nums.text(x=0.6, y=0.8, s='ATTACK', va='center_baseline', **CONFIG))
        self._nums.append(self.ax_nums.text(x=0.6, y=0.75, s=f"{total*100:.1f}%", fontsize=20, va='top', **CONFIG))
        
        self._nums.append(self.ax_nums.text(x=0.3, y=0.62, s='GOOD', va='center_baseline', ha='center'))
        self._nums.append(self.ax_nums.text(x=0.3, y=0.60, s=f"{good*100:.1f}%", fontsize=12, va='top', **CONFIG))
    
        self._nums.append(self.ax_nums.text(x=0.9, y=0.62, s='ERROR', va='center_baseline', ha='center'))
        self._nums.append(self.ax_nums.text(x=0.9, y=0.60, s=f"{error*100:.1f}%", fontsize=12, va='top', **CONFIG))
        
        self._nums.append(self.ax_nums.text(x=0.6, y=0.4, s='TIP', va='center_baseline', **CONFIG))
        self._nums.append(
            self.ax_nums.text(
                x=0.6, y=0.35,
                s=f"{tips*100:.1f}%",
                fontsize=20,
                va='top',
                bbox={'facecolor': 'white', 'edgecolor': 'red', 'linewidth': 2} if tips > self._MIN_TIPS else None,
                **CONFIG
            )
        )
    

    def create_scatter(self, hit: HitEnum, ext: ExtEnum, zone: ZoneEnum, count: int) -> None:
        style = self._MRK_STYLES[(legend := ext or hit)]
        mrk = style['marker']
        mrk_color = style['color']
        mrk_size = style['markersize']

        x, y = self._ZONE_SQUARES[zone]
        x_points = np.random.uniform(*x, count)
        y_points = np.random.uniform(*y, count)

        scatter = self.ax_scatter.scatter(
            x_points, y_points,
            s=mrk_size ** 2,
            c=mrk_color,
            marker=mrk
        )
        marker = Line2D([], [], marker=mrk, markersize=mrk_size, color=mrk_color, linestyle='none')

        if legend.name[0] in 'KQ':
            self._scatters.append(
                (
                    scatter,
                    self.ax_scatter.scatter(
                        x_points, y_points,
                        s=10 ** 2,
                        marker='s',
                        fc='none',
                        ec=mrk_color
                    )
                )
            )
            #handle?
        else:
            self._scatters.append(scatter)
            #handle?
        self._legends.add(legend)
        self._counts[legend] = self._counts.get(legend, 0) + count
        #self._handles?
    

    def _create_legends(self) -> None:
        if not (legends := self._legends):
            return
        legends = sorted(legends)

        handles = []
        for lgd in legends:
            style = self._MRK_STYLES[lgd]
            mrk = style['marker']
            mrk_color = style['color']
            mrk_size = style['markersize']

            marker = Line2D(
                [], [],
                linestyle='none',
                color=mrk_color,
                marker=mrk,
                markersize=mrk_size
            )
            if lgd.name[0] in 'KQ':
                handles.append(
                    (
                        marker,
                        Line2D(
                            [], [],
                            marker='s',
                            markersize=10,
                            linestyle='none',
                            markerfacecolor='none',
                            markeredgecolor=mrk_color
                        )
                    )
                )
            else:
                handles.append(marker)
        
        self.ax_scatter.legend(
            handles=handles,
            labels=[f"{lgd}: {self._counts[lgd]}" for lgd in legends],
            loc='upper left',
            bbox_to_anchor=(1, 0.9),
            title='ATTACKS',
            title_fontproperties = {'weight': 'bold'}
        )
    

    def clear_axes(self) -> None:
        self._legends.clear()
        self._counts.clear()
        if (lgd := self.ax_scatter.get_legend()) is not None:
            lgd.remove()

        for attr in (self._arrow_lbls, self._arrows, self._nums):
            for item in attr:
                item.remove()
            attr.clear()
        
        for item in [x for y in self._scatters for x in (y if isinstance(y, tuple) else (y,))]:
            item.remove()
        self._scatters.clear()
    

    def save_bytes(self) -> BytesIO:
        self._create_legends()
        return super().save_bytes()
    

    def save_image(self, path: Path) -> None:
        self._create_legends()
        return super().save_image(path)
    

    def set_title(self, title: str, highlight: bool=False) -> None:
        if highlight:
            color = Colors.WHITE
            bbox = {'fc': Colors.RED, 'ec': 'none'}
        else:
            color = Colors.BLACK
            bbox = {'fc': 'none', 'ec': 'none'}
        self.suptitle(
            title, y=0.85, size='x-large', weight='bold', color=color, bbox = bbox
        )