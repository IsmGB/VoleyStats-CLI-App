import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import colorsys
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.text import Text, Annotation
from matplotlib.lines import Line2D
from matplotlib.collections import LineCollection, PathCollection
from matplotlib.container import PieContainer, BarContainer
from matplotlib.patches import ArrowStyle, FancyArrowPatch, Rectangle
from matplotlib.ticker import MaxNLocator
from matplotlib.transforms import ScaledTranslation, Transform
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageOps, ImageChops
from pandas import DataFrame
import numpy as np
from numpy.typing import ArrayLike, NDArray
from abc import ABC, abstractmethod

from typing import Iterable, Sequence, Literal, Callable
from dataclasses import dataclass, field


from voleystats.data_classes import *

TEST_IMG = Path(__file__).resolve().parents[2] / "tmp" / "test_fig.png" # debug images


MRK_SQUARE = {'marker': 's', 'markersize': 10, 'fillstyle': 'none'}
COLORS = {
    'blue': '#0057B8',
    'orange': '#E69F00',
    'green': '#236121',
    'red': '#C00000',
    'purple': '#6A3D9A',
    'cyan': '#17BECF',
    'brown': '#8C564B',
    'grey': '#4D4D4D',
    'lime': '#06A529',
    'black': '#000000',
    'light_grey': '#A0A0A0'
}
MRK_STYLES: dict[NmonHit|NmonExt, dict[str, int|str]] = {
    NmonHit.HIGH: {'marker': '$H$', 'color': COLORS['purple'], 'markersize': 6},
    NmonHit.MEDIUM: {'marker': '$M$', 'color': COLORS['orange'], 'markersize': 6},
    NmonHit.FAST: {'marker': '$N$', 'color': COLORS['blue'], 'markersize': 6},
    NmonHit.OTHER: {'marker': '$O$', 'color': COLORS['brown'], 'markersize': 6},
    NmonHit.QUICK: {'marker': '$Q$', 'color': COLORS['lime'], 'markersize': 6},
    NmonHit.TENSE: {'marker': '$T$', 'color': COLORS['red'], 'markersize': 6},
    NmonHit.SUPER: {'marker': '$U$', 'color': COLORS['grey'], 'markersize': 6},
    NmonExt.X1: {'marker': 'v', 'color': COLORS['blue'], 'markersize': 6},
    NmonExt.X2: {'marker': 'P', 'color': COLORS['orange'], 'markersize': 6},
    NmonExt.X3: {'marker': 's', 'color': COLORS['green'], 'markersize': 6},
    NmonExt.X4: {'marker': 'o', 'color': COLORS['red'], 'markersize': 6},
    NmonExt.X5: {'marker': 'X', 'color': COLORS['purple'], 'markersize': 6},
    NmonExt.X6: {'marker': '^', 'color': COLORS['cyan'], 'markersize': 6},
    NmonExt.X7: {'marker': 'D', 'color': COLORS['brown'], 'markersize': 6},
    NmonExt.X8: {'marker': 'd', 'color': COLORS['grey'], 'markersize': 6},
    NmonExt.X9: {'marker': '*', 'color': COLORS['lime'], 'markersize': 8},
    NmonExt.K1: {'marker': 'X', 'color': COLORS['purple'], 'markersize': 6},
    NmonExt.K2: {'marker': 'P', 'color': COLORS['orange'], 'markersize': 6},
    NmonExt.K3: {'marker': 'v', 'color': COLORS['blue'], 'markersize': 6},
    NmonExt.K4: {'marker': 'o', 'color': COLORS['red'], 'markersize': 6},
    NmonExt.K5: {'marker': '^', 'color': COLORS['cyan'], 'markersize': 6},
    NmonExt.K6: {'marker': '<', 'color': COLORS['lime'], 'markersize': 6},
    NmonExt.K7: {'marker': 'd', 'color': COLORS['grey'], 'markersize': 6},
    NmonExt.K8: {'marker': 'D', 'color': COLORS['brown'], 'markersize': 6},
    NmonExt.K9: {'marker': '>', 'color': COLORS['green'], 'markersize': 6},
    NmonExt.NONE: {'marker': '.', 'color': COLORS['black'], 'markersize': 6}
}

MRK_RANGES = ((0.22, 0.38), (0.42, 0.58), (0.62, 0.78))
MRK_ZONES: dict[NmonZone, tuple[tuple[float, float], tuple[float, float]]] = {
    NmonZone.Z1: (MRK_RANGES[2], MRK_RANGES[0]), # ((xmin, xmax), (ymin, ymax))
    NmonZone.Z2: (MRK_RANGES[2], MRK_RANGES[2]),
    NmonZone.Z3: (MRK_RANGES[1], MRK_RANGES[2]),
    NmonZone.Z4: (MRK_RANGES[0], MRK_RANGES[2]),
    NmonZone.Z5: (MRK_RANGES[0], MRK_RANGES[0]),
    NmonZone.Z6: (MRK_RANGES[1], MRK_RANGES[0]),
    NmonZone.Z7: (MRK_RANGES[0], MRK_RANGES[1]),
    NmonZone.Z8: (MRK_RANGES[1], MRK_RANGES[1]),
    NmonZone.Z9: (MRK_RANGES[2], MRK_RANGES[1])
}

ARROW_NET = {2: (0.28, 0.85), 3: (0.5, 0.85), 4: (0.72, 0.85)}
ARROW_START: dict[NmonExt, int] = {
    NmonExt.X1: 0,
    NmonExt.X2: 0,
    NmonExt.X3: 2,
    NmonExt.X4: 2,
    NmonExt.X5: 2,
    NmonExt.X6: 3,
    NmonExt.X7: 2,
    NmonExt.X8: 0,
    NmonExt.X9: 1,
    NmonExt.K1: 1,
    NmonExt.K2: 1,
    NmonExt.K3: 1,
    NmonExt.K4: 1,
    NmonExt.K5: 1,
    NmonExt.K6: 1,
    NmonExt.K7: 1,
    NmonExt.K8: 1,
    NmonExt.K9: 0,
    NmonExt.NONE: -1,
}
ARROW_ENDS: dict[NmonZone, tuple[float,float]] = {
    NmonZone.Z1: (0.7, 0.3),
    NmonZone.Z2: (0.7, 0.7),
    NmonZone.Z3: (0.5, 0.7),
    NmonZone.Z4: (0.3, 0.7),
    NmonZone.Z5: (0.3, 0.3),
    NmonZone.Z6: (0.5, 0.3),
    NmonZone.Z7: (0.3, 0.5),
    NmonZone.Z8: (0.5, 0.5),
    NmonZone.Z9: (0.7, 0.5)
}
ARROW_LABELS: dict[NmonZone, tuple[float,float]] = {
    NmonZone.Z1: (0.7, 0.21),
    NmonZone.Z2: (0.7, 0.61),
    NmonZone.Z3: (0.5, 0.61),
    NmonZone.Z4: (0.3, 0.61),
    NmonZone.Z5: (0.3, 0.21),
    NmonZone.Z6: (0.5, 0.21),
    NmonZone.Z7: (0.3, 0.41),
    NmonZone.Z8: (0.5, 0.41),
    NmonZone.Z9: (0.7, 0.41)
}
ARROW_COLORS: dict[NmonZone, str] = {
    NmonZone.Z1: "#0072B2",
    NmonZone.Z2: "#E69F00",
    NmonZone.Z3: "#009E73",
    NmonZone.Z4: "#5911B8",
    NmonZone.Z5: "#E26607",
    NmonZone.Z6: "#56B4E9",
    NmonZone.Z7: "#6B8E23",
    NmonZone.Z8: "#8C564B",
    NmonZone.Z9: "#C2185B",
}

def get_color_shades(color: str, num: int) -> list[str]:
    h, l, s = colorsys.rgb_to_hls(*mcolors.to_rgb(color))
    if num == 1:
        return [mcolors.to_hex(colorsys.hls_to_rgb(h, 0.6, s))]
    
    lmin, lmax = 0.4, 0.8
    l_shades = [lmax - n * (lmax-lmin) / (num - 1) for n in range(num)]
    return [mcolors.to_hex(colorsys.hls_to_rgb(h, shade, s)) for shade in l_shades]


class BaseFigure(ABC):
    def __init__(self, figure: Figure) -> None:
        super().__init__()
        self.figure = figure
        self.figure.patch.set_edgecolor('black')
        self.figure.patch.set_linewidth(3)
    

    @abstractmethod
    def clear_axes(self) -> None:
        pass


    # def set_title(self, title: str) -> None:
    #     self.figure.suptitle(title, y=0.95, size='x-large', weight='bold')


    def show(self) -> None:
        plt.show()


    def save_bytes(self) -> BytesIO:
        img = BytesIO()
        self.figure.savefig(img, format='png', bbox_inches='tight')
        plt.close(self.figure)
        # return self._crop_and_border(img)
        return img
    

    def save_image(self, path: Path) -> None:
        self.figure.savefig(TEST_IMG)
        plt.close(self.figure)
    

    def _crop_and_border(self, img_bytes: BytesIO, margin: int=20):
        img_bytes.seek(0)
        # Crop image
        img = Image.open(img_bytes).convert("RGB")
        bg = Image.new("RGB", img.size, img.getpixel((0, 0)))
        bbox = ImageChops.difference(img, bg).getbbox()
        if bbox:
            bbox = (
                max(0, bbox[0] - margin),
                max(0, bbox[1] - margin),
                min(img.width, bbox[2] + margin),
                min(img.height, bbox[3] + margin)
            )
            img = img.crop(bbox)
        # Add border
        img = ImageOps.expand(img, border=2, fill='black')
        # Return bytes
        img_bytes = BytesIO()
        img.save(img_bytes, format='png')
        return img_bytes




class CourtFigure(BaseFigure):
    """Figure to plot attack distribution"""
    def __init__(self) -> None:
        left, top, right, bottom = 0.02, 0.12, 0.12, 0
        width = 1 - left - right
        height = 1 - top - bottom
        w1, w2 = width * 0.4, width * 0.2

        figH = 4
        figW = 4 * (height / (0.4*width))

        super().__init__(
            figure=plt.figure(figsize=(figW, figH))
        )

        self.ax_arrows = self.figure.add_axes((left, bottom, w1, height))
        self.ax_nums = self.figure.add_axes((left+w1, bottom, w2, height))
        self.ax_scatter = self.figure.add_axes((left+w1+w2, bottom, w1, height))

        self._set_axes()
        self._draw_court(self.ax_arrows)
        self._draw_court(self.ax_scatter)

        self._scatters: list[PathCollection|tuple[PathCollection, PathCollection]] = list()
        self._legends: set[NmonHit|NmonExt] = set()
        # self._legends: set[tuple[NmonHit|NmonExt, Line2D|tuple[Line2D, Line2D]]] = set()
        self._arrows: list[FancyArrowPatch] = list()
        self._arrow_texts: list[Text] = list()
        self._nums: list[Text] = list()
        self._counts: dict[NmonHit|NmonExt, int] = dict()
    

    def _set_axes(self) -> None:
        for ax in (self.ax_arrows, self.ax_scatter):
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
        
        self.ax_nums.set_xlim(0, 1.2)
        self.ax_nums.set_ylim(0, 1)
        self.ax_nums.axis('off')
    

    def _draw_court(self, axes: Axes) -> None:
        boundary = [
            {'line': [(0.2, 0.8), (0.2, 0.2)], 'lw': 2, 'ls': 'solid'}, # left
            {'line': [(0.2, 0.2), (0.8, 0.2)], 'lw': 2, 'ls': 'solid'}, # bottom
            {'line': [(0.8, 0.2), (0.8, 0.8)], 'lw': 2, 'ls': 'solid'}, # right
            {'line': [(0.2, 0.6), (0.8, 0.6)], 'lw': 2, 'ls': 'solid'}, # defense
            {'line': [(0.1, 0.8), (0.9, 0.8)], 'lw': 4, 'ls': 'solid'}, # net
            {'line': [(0.13, 0.6), (0.87, 0.6)], 'lw': 1.5, 'ls': 'dashed'}, # defense dashed
            {'line': [(0.2, 0.185), (0.2, 0.17)], 'lw': 2, 'ls': 'solid'}, # left serve dot
            {'line': [(0.8, 0.185), (0.8, 0.17)], 'lw': 2, 'ls': 'solid'}, # right serve dot
        ]
        grid = [
            [(0.4, 0.8), (0.4, 0.2)], # separator 5-6
            [(0.6, 0.8), (0.6, 0.2)], # separator 6-1
            [(0.2, 0.4), (0.8, 0.4)], # separator defense
        ]

        axes.add_collection(
            LineCollection(
                segments=[v['line'] for v in boundary],
                colors='black',
                linewidths=[v['lw'] for v in boundary],
                linestyles=[v['ls'] for v in boundary],
                zorder=0
            )
        )
        axes.add_collection(
            LineCollection(
                segments=grid,
                colors=COLORS['light_grey'],
                linewidths=0.6,
                linestyles='dashed',
                zorder=0
            )
        )
        # axes.set_ylim(-0.15, 0.85)
    

    def create_arrow(self, net: int, zone: NmonZone, percent: float) -> None:
        if not zone:
            return

        arrow = FancyArrowPatch(
            posA=ARROW_NET.get(net),
            posB=ARROW_ENDS[zone],
            arrowstyle=ArrowStyle(
                stylename="Simple",
                head_length=1.2,
                head_width=1.2,
                tail_width=0.5
            ),
            mutation_scale=25 if percent > 0.5 else (15 if percent > 0.2 else 10),
            color=ARROW_COLORS[zone],
            zorder=(1 - percent) * 100
        )
        self.ax_arrows.add_patch(arrow)
        self._arrows.append(arrow)

        x, y = ARROW_LABELS[zone]
        self._arrow_texts.append(
            self.ax_arrows.text(
                x=x,
                y=y,
                s=f"{percent*100:.1f}%",
                fontweight='bold',
                ha='center',
                va='baseline',
                zorder=100
            )
        )
    

    def print_attack_vs_tip(self, attack_per: float|tuple[float, float, float], tip_per: float) -> None:
        attack_per, eff_per, err_per = attack_per if isinstance(attack_per, tuple) else (attack_per, None, None)
        config: dict[str, Any] = {'weight': 'bold', 'ha': 'center'}

        self._nums.append(self.ax_nums.text(x=0.6, y=0.8, s='ATTACK', va='center_baseline', **config))
        self._nums.append(self.ax_nums.text(x=0.6, y=0.75, s=f"{attack_per*100:.1f}%", fontsize=20, va='top', **config))
        
        if eff_per is not None:
            self._nums.append(self.ax_nums.text(x=0.3, y=0.62, s='GOOD', va='center_baseline', ha='center'))
            self._nums.append(self.ax_nums.text(x=0.3, y=0.60, s=f"{eff_per*100:.1f}%", fontsize=12, va='top', **config))
        
        if err_per is not None:
            self._nums.append(self.ax_nums.text(x=0.9, y=0.62, s='ERROR', va='center_baseline', ha='center'))
            self._nums.append(self.ax_nums.text(x=0.9, y=0.60, s=f"{err_per*100:.1f}%", fontsize=12, va='top', **config))
        
        self._nums.append(self.ax_nums.text(x=0.6, y=0.4, s='TIP', va='center_baseline', **config))
        self._nums.append(
            self.ax_nums.text(
                x=0.6, y=0.35,
                s=f"{tip_per*100:.1f}%",
                fontsize=20,
                va='top',
                bbox={'facecolor': 'white', 'edgecolor': 'red', 'linewidth': 2} if tip_per > 0.35 else None, # config value
                **config
            )
        )

    
    def create_scatter(self, hit: NmonHit, ext: NmonExt, zone: NmonZone, count: int) -> None:
        if not zone:
            return
        
        legend = ext or hit
        x, y = MRK_ZONES[zone]
        style = MRK_STYLES[legend]

        x_points = np.random.uniform(*x, count)
        y_points = np.random.uniform(*y, count)

        scatter = self.ax_scatter.scatter(
            x=x_points,
            y=y_points,
            s=style['markersize'] ** 2, # type: ignore
            c=style['color'],
            marker=style['marker'] # type: ignore
        )
        marker = Line2D([], [], marker=style['marker'], markersize=style['markersize'], color=style['color'], linestyle='none')
        if legend.name[0] in 'KQ':
            self._scatters.append(
                (
                    scatter,
                    self.ax_scatter.scatter(
                        x=x_points,
                        y=y_points,
                        s=10 ** 2,
                        marker='s',
                        fc='none',
                        ec=style['color'],
                    )
                )
            )
            handle = (
                marker,
                Line2D([], [], marker='s', markersize=10, markerfacecolor='none', markeredgecolor=style['color'], linestyle='none')
            )
        else:
            self._scatters.append(scatter)
            handle = marker

        self._legends.add(legend)
        self._counts[legend] = self._counts.get(legend, 0) + count

        self._handles = {}
    

    def create_legends(self) -> None:
        if not (legends := self._legends):
            return
        legends = sorted(legends)
        
        handles = []
        for lgd in legends:
            style = MRK_STYLES[lgd]
            marker = Line2D(
                [], [],
                linestyle='none',
                color=style['color'],
                marker=style['marker'],
                markersize=style['markersize']
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
                            markeredgecolor=style['color']
                        )
                    )
                )
            else:
                handles.append(marker)

        self.ax_scatter.legend(
            handles=handles,
            labels=[f"{lgd}: {self._counts[lgd]}" for lgd in legends],
            loc='upper left',
            bbox_to_anchor=(1, 1),
            title='ATTACKS',
            title_fontproperties = {'weight': 'bold'}
        )
        return
        self.ax_scatter.legend(
            handles=self._scatters,
            labels=[f"{lbl}: {self._counts[lbl]}" for lbl in self._legends],
            loc='upper left',
            bbox_to_anchor=(1, 1),
            title='ATTACKS',
            title_fontproperties = {'weight': 'bold'}
        )
    

    def clear_axes(self) -> None:
        self._legends.clear()
        self._counts.clear()
        if (lgd := self.ax_scatter.get_legend()) is not None:
            lgd.remove()

        for attr in (self._arrow_texts, self._arrows, self._nums):
            for item in attr:
                item.remove()
            attr.clear()
        
        for item in [x for y in self._scatters for x in (y if isinstance(y, tuple) else (y,))]:
            item.remove()
        self._scatters.clear()
    

    def set_title(self, title: str, highlight: bool=False) -> None:
        color, bbox = ('#ffffff', {'fc': '#ff0000', 'ec': 'none'}) if highlight else ('#000000', {'fc': 'none', 'ec': 'none'})
        self.figure.suptitle(
            title,
            y=0.85,
            size='x-large',
            weight='bold',
            color=color,
            bbox = bbox
        )



class PieFigure(BaseFigure):
    def __init__(self) -> None:
        super().__init__(figure=plt.figure(figsize=(4,4)))
        self.ax_pie = self.figure.add_subplot()

        self._pies: list[PieContainer] = []
    

    def _clear_zeros(self, values: Sequence[float], labels: Sequence[Any], colors: Sequence[str]=[]) -> tuple[list[Any], ...]:
        if (nval:=len(values)) != len(labels) or nval != len(colors):
            raise ValueError("Length of values, labels and colors must be the same.")
        grps = [(v,l,c) for v,l,c in zip(values, labels, colors) if v!=0]
        return ([], [], []) if not grps else tuple(list(grp) for grp in zip(*grps))
    

    def make_pie(self, values: Sequence[float], labels: Sequence[str], colors: Sequence[str]=[], count: bool=True) -> None:
        if count:
            total = sum(values)
            autopct = lambda pct: f"{pct:.1f}% / {round(pct * total / 100)}"
        else:
            autopct = '%1.1f%%'

        values, labels, colors = self._clear_zeros(values, labels, colors)
        pie = self.ax_pie.pie(
            x=values,
            labels=labels,
            autopct=autopct,
            wedgeprops={'edgecolor': 'white'},
            colors=colors if colors else None
        )
        for pct in pie[2]:
            pct.set_fontsize(9)
            pct.set_fontweight('bold')
        self._pies.append(pie)
    

    # def make_pie(self, values: Sequence[int|float], labels: list[str]) -> None:
    #     values, labels = self._clean_zeros(values, labels)
    #     self._pies.append(
    #         self.ax_pie.pie(
    #             x=values,
    #             labels=labels,
    #             autopct='%1.1f%%',
    #             wedgeprops={'edgecolor': 'white'}
    #         )
    #     )
    

    def make_pie_hit(self, values: list[int|float], labels: list[NmonHit|NmonExt]) -> None:
        values, labels, _ = self._clear_zeros(values, labels, ["#000000"] * len(values))
        self._pies.append(
            self.ax_pie.pie(
                x=values,
                labels=labels,
                colors=[MRK_STYLES[lbl]['color'] for lbl in labels], # type: ignore
                autopct='%1.1f%%',
                wedgeprops={'edgecolor': 'white'}
            )
        )
    

    # def make_pie_values(self, values: Sequence[float]) -> None:
    #     if len(values) != len(NmonValue):
    #         raise ValueError
        
    #     # colors = ['#00B050', '#66C24A', '#FFD966', '#F6B26B', '#E06666', '#C00000']
    #     colors = ["#077237", '#66C24A', '#FFD966', "#E6A056", '#E06666', "#8D0808"]
    #     values, labels, colors = self._clean_zeros(values, [e.value for e in NmonValue], colors)
    #     self._pies.append(
    #         self.ax_pie.pie(
    #             x=values,
    #             labels=labels,
    #             autopct='%1.1f%%',
    #             wedgeprops={'edgecolor': 'white'},
    #             colors=colors
    #         )
    #     )
    

    def make_donut(
        self,
        outer_val: list[int|float],
        outer_lbl: list[str],
        inner_val: list[int|float],
        inner_lbl: list[str],
        outer_color=None,
        inner_color=None
        ) -> None:
        self._pies.append(
                self.ax_pie.pie(
                x=outer_val,
                labels=outer_lbl,
                autopct=lambda pct: f'{pct*sum(outer_val)/100:.0f}',
                pctdistance=0.68,
                labeldistance=1.1,
                radius=1,
                wedgeprops={'edgecolor': 'white', 'width': 0.25},
                colors=outer_color
            )
        )

        self._pies.append(
            self.ax_pie.pie(
                x=inner_val,
                labels=inner_lbl,
                autopct=lambda pct: f'{pct*sum(inner_val)/100:.0f}',
                # pctdistance=1.05,
                labeldistance=2.75,
                radius=0.6,
                wedgeprops={'edgecolor': 'white'},
                colors=inner_color,
                textprops={
                    'fontweight': 'bold',
                    'ha': 'center'
                }
            )
        )
        # self.figure.set_size_inches(8, 7.2)
        # self.figure.subplots_adjust(top=0.75, bottom=0.25)
    

    def clear_axes(self) -> None:
        self.ax_pie.set_title('')
        for pie in self._pies:
            pie.remove()
        self._pies.clear()
    

    def set_title(self, title):
        self.ax_pie.set_title(title)
    


class BarFigure(BaseFigure):
    @dataclass
    class BarsGroup:
        names: list[str]
        values: NDArray[Any]
        colors: list[str]
    
        # def __post_init__(self) -> None:
        #     w, h = self.values.shape
        #     n_names = len(self.names)
        #     n_colors = len(self.colors)
        #     if h != n_names:
        #         raise ValueError(f"{n_names} names were provided. Expected {h}.")
        #     if h != n_colors:
        #         raise ValueError(f"{n_colors} colors were provided. Expected {h}")
        
        @property
        def shape(self) -> tuple[int,int]:
            return self.values.shape

    
    def __init__(self) -> None:
        super().__init__(figure=plt.figure())
        self.ax_bar = self.figure.add_subplot()

        self._bars: list[BarContainer] = []
        self._bar_labels: list[list[Annotation]] = []
        self._bar_totals: list[Text] = []
    

    def _set_up_bars(self, labels: list, groups: Sequence, width: float, space: float) -> tuple[int, NDArray, NDArray, NDArray]:
        nlbl, ngrp = len(labels), len(groups)
        idx, delta = np.arange(nlbl), np.arange(ngrp)

        ticks = idx * space
        pos = np.empty((ngrp, nlbl))
        for i in delta:
            for j in idx:
                pos[i, j] = ticks[j] + width * (delta[i] - (ngrp-1)/2)
        
        # w, h = self.figure.get_size_inches()
        # self.figure.set_size_inches(w, h + max(0, nlbl) * 0.35)
        
        return nlbl, ticks, pos, np.zeros((ngrp, nlbl)) # (ticks pos, bar pos, bar origins)


    def _set_bars_total(self, values: NDArray, x: NDArray, y: NDArray, transform: Transform) -> None:
        self._bar_totals.extend(
            [
                self.ax_bar.text(
                    x=x[i], y=y[i], s=str(total), 
                    weight='bold', size=12, va='center', ha='center',
                    transform=transform
                )
                for i,total in enumerate(values.sum(axis=1))
            ]
        )
    
    def _set_legend(self, groups: Sequence[BarsGroup]) -> None:
        legend = [x for y in [item.names for item in groups] for x in y]
        self.ax_bar.legend(labels=legend, loc='upper left', bbox_to_anchor=(1, 1))
    

    def _make_bars(self, ax_bar_func: Callable, values: NDArray, colors: list, pos: NDArray, base: NDArray, width: float) -> None:
        for v, c in zip(values.T, colors):
            bar = ax_bar_func(pos, v, width, base, color=c)
            base += v
            self._bar_labels.append(
                self.ax_bar.bar_label(bar, label_type='center', labels=["" if x==0 else x for x in v])
            )
            self._bars.append(bar)

    
    def make_horizontal_bars(self, labels: list[str], groups: Sequence[BarsGroup], height: float=0.5, vspace: float=1) -> None:        
        nlbl, y, ypos, left = self._set_up_bars(labels, groups, height, vspace)
        baseline = np.zeros(nlbl)
        transform = self.ax_bar.get_yaxis_transform() + ScaledTranslation(-10/72, 0, self.figure.dpi_scale_trans)
        i = 0
        for item in groups:
            values = item.values
            ypos_i = ypos[i, :]
            self._make_bars(self.ax_bar.barh, values, item.colors, ypos_i, left[i, :], height)
            self._set_bars_total(values, baseline, ypos_i, transform)
            i+=1
        self._set_legend(groups)

        self.ax_bar.set_yticks(y)
        self.ax_bar.set_yticklabels(labels)

        w, h = self.figure.get_size_inches()
        self.figure.set_size_inches(w, max(h, nlbl * 1))
    

    def make_vertical_bars(self, labels: list[str], groups: Sequence[BarsGroup], width: float=0.5, hspace: float=1) -> None: 
        nlbl, x, xpos, bottom = self._set_up_bars(labels, groups, width, hspace)
        baseline = np.zeros(nlbl)
        transform = self.ax_bar.get_xaxis_transform() + ScaledTranslation(0, -10/72, self.figure.dpi_scale_trans)
        i = 0
        for item in groups:
            values = item.values
            xpos_i = xpos[i, :]
            self._make_bars(self.ax_bar.bar, values, item.colors, xpos_i, bottom[i, :], width)
            self._set_bars_total(values, xpos_i, baseline, transform)
            i+=1
        self._set_legend(groups)

        self.ax_bar.set_xticks(x)
        self.ax_bar.set_xticklabels(labels)

        w, h = self.figure.get_size_inches()
        self.figure.set_size_inches(max(w, nlbl), h)


    def set_axes(self, config: str) -> None:
        self.ax_bar.relim()
        self.ax_bar.autoscale_view()
        self.ax_bar.set_axisbelow(True)
        match config:
            case 'horizontal_bars':
                self.ax_bar.yaxis.set_inverted(True)        
                self.ax_bar.grid(True, axis='x')
                self.ax_bar.tick_params(axis='x', bottom=False, labelbottom=False)
                self.ax_bar.tick_params(axis='y', width=1.5, pad=20)
                self.ax_bar.spines['left'].set_linewidth(1.5)
                # for side in ('top', 'right, 'bottom'):
                    # self.ax_bar.spines[side].set_visible(False)
                self.ax_bar.xaxis.set_major_locator(MaxNLocator(integer=True))
            case 'vertical_bars':
                self.ax_bar.grid(True, axis='y')
                self.ax_bar.tick_params(axis='y', left=False, labelleft=False)
                self.ax_bar.tick_params(axis='x', width=1.5, pad=15, labelrotation=45)
                self.ax_bar.spines['bottom'].set_linewidth(1.5)
                # for side in ('top', 'left', 'right'):
                #     self.ax_bar.spines[side].set_visible(False)
                self.ax_bar.yaxis.set_major_locator(MaxNLocator(integer=True))
            case _:
                pass
    
    def set_title(self, title):
        self.ax_bar.set_title(title)


    def clear_axes(self) -> None:
        for attr in (self._bars, self._bar_totals):
            for item in attr:
                item.remove()
            attr.clear()

        for item in self._bar_labels:
            for annot in item:
                annot.remove()
        self._bar_labels.clear()



if __name__ == '__main__':
    # TEST COURFIGURE
    # fig = CourtFigure()
    # fig.create_arrow(4, NmonZone.Z5, 0.5)
    # fig.print_attack_vs_tip((0.75, 1, 1), 0.25)
    # fig.create_scatter(NmonHit.HIGH, NmonExt.X5, NmonZone.Z5, count=7)
    # fig.create_scatter(NmonHit.HIGH, NmonExt.X5, NmonZone.Z6, count=2)
    # fig.create_scatter(NmonHit.QUICK, NmonExt.K2, NmonZone.Z1, count=3)
    # fig.create_legends()
    # fig.set_title("Dirección de ataque por 4 del jugador 7 Padilla P")

    # TEST PIEFIGURE
    # fig = PieFigure()
    # fig.make_pie2([1,2,3,4,5,6], ['uno', 'dos', 'trés', 'cuatro', 'cinco', 'seis'], ['#cc0000', '#00dd00', '#0000ff'])
    # fig.set_title("TITULO TITULO")

    # TEST BARS
    fig = BarFigure()
    bars = {'v': (fig.make_vertical_bars, 'vertical_bars'), 'h': (fig.make_horizontal_bars, 'horizontal_bars')}
    k = 'h'
    bars[k][0](
        labels=['pedro', 'ismael', 'david'],
        groups=[
            BarFigure.BarsGroup(
                names=[e.name for e in [NmonSkill.ATTACK, NmonSkill.SERVE, NmonSkill.BLOCK]],
                values=np.array([[7, 7, 7], [1, 2, 3], [2, 3, 4]]),
                colors=['#00ff00', '#009900', '#003300']
            ),
            BarFigure.BarsGroup(
                names=[e.name for e in [NmonSkill.ATTACK, NmonSkill.SERVE, NmonSkill.BLOCK, NmonSkill.RECEIVE, NmonSkill.SET]],
                values=np.array([[7, 7, 7, 6, 8], [1, 2, 3, 1, 2], [9, 8, 5, 3, 2]]),
                colors=['#ff0000', '#aa0000', '#770000', '#550000', '#330000']
            )
        ],
        # width=0.5,
        # hspace=2
    )
    fig.set_axes(bars[k][1])
    fig.set_title("Puntos frente a errores")


    fig.show()
    # fig.save_image(TEST_IMG)