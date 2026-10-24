import numpy as np
from numpy.typing import NDArray
from matplotlib.container import BarContainer
from matplotlib.text import Annotation, Text
from matplotlib.ticker import MaxNLocator
from matplotlib.transforms import ScaledTranslation, Transform
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Callable

from .base_figure import *


@dataclass
class BarsGroup:
    names: list[str]
    values: NDArray
    colors: list[str]



class BarFigure(BaseFigure, ABC):
    def __init__(self) -> None:
        super().__init__()
        self.ax_bar = self.add_subplot()

        self._bars: list[BarContainer] = list()
        self._labels: list[list[Annotation]] = list()
        self._totals: list[Text] = list()
    

    @abstractmethod
    def make_bars(self, labels: list[str], groups: list[BarsGroup], width: float, space: float) -> None:
        pass
    

    @abstractmethod
    def set_axes(self) -> None:
        self.ax_bar.relim()
        self.ax_bar.autoscale_view()
        self.ax_bar.set_axisbelow(True)
    

    def _set_bars(self, nlbl: int, ngrp: int, width: float, space: float) -> list[NDArray]:
        idx, delta = np.arange(nlbl), np.arange(ngrp)
        ticks = idx * space
        pos = np.empty((ngrp, nlbl))
        for i in delta:
            for j in idx:
                pos[i, j] = ticks[j] + width * (delta[i] - (ngrp-1)/2)
        return [ticks, pos, np.zeros((ngrp, nlbl))] # [ticks pos, bar pos, bar origins]
    

    def _set_total_values(self, values: NDArray, x: NDArray, y: NDArray, transform: Transform) -> None:
        self._totals.extend(
            [
                self.ax_bar.text(
                    x=x[i], y=y[i], s=str(total), 
                    weight='bold', size=12, va='center', ha='center',
                    transform=transform
                )
                for i,total in enumerate(values.sum(axis=1))
            ]
        )
    

    def _set_legend(self, values: list[list[str]]) -> None:
        legend = [x for y in values for x in y]
        self.ax_bar.legend(labels=legend, loc='upper left', bbox_to_anchor=(1, 1))
    

    def _make_bars_level(self, ax_bar_func: Callable, values: NDArray, colors: list[str], pos: NDArray, base: NDArray, width: float) -> None:
        for v, c in zip(values.T, colors):
            bar = ax_bar_func(pos, v, width, base, color=c)
            base += v
            self._labels.append(
                self.ax_bar.bar_label(
                    container=bar, label_type='center', labels=["" if x==0 else x for x in v])
            )
            self._bars.append(bar)


    def set_title(self, title: str) -> None:
        self.ax_bar.set_title(title)
    

    def clear_axes(self) -> None:
        for attr in (self._bars, self._totals):
            for item in attr:
                item.remove()
            attr.clear()

        for item in self._labels:
            for annot in item:
                annot.remove()
        self._labels.clear()



class VBarFigure(BarFigure):
    def __init__(self) -> None:
        super().__init__()
    

    def make_bars(self, labels: list[str], groups: list[BarsGroup], width: float, space: float) -> None:
        nlbl = len(labels)
        baseline = np.zeros(nlbl)
        x, xpos, bottom = self._set_bars(nlbl, len(groups), width, space)
        transform = self.ax_bar.get_xaxis_transform() + ScaledTranslation(0, -10/72, self.dpi_scale_trans)

        i = 0
        for item in groups:
            values = item.values
            xpos_i = xpos[i, :]
            self._make_bars_level(self.ax_bar.bar, values, item.colors, xpos_i, bottom[i, :], width)
            self._set_total_values(values, xpos_i, baseline, transform)
            i += 1
        self._set_legend([item.names for item in groups])
        
        self.ax_bar.set_xticks(x)
        self.ax_bar.set_xticklabels(labels)

        w, h = self.get_size_inches()
        self.set_size_inches(max(w, nlbl), h)
    

    def set_axes(self) -> None:
        super().set_axes()
        self.ax_bar.grid(True, axis='y')
        self.ax_bar.tick_params(axis='y', left=False, labelleft=False)
        self.ax_bar.tick_params(axis='x', width=1.5, pad=15, labelrotation=45)
        self.ax_bar.spines['bottom'].set_linewidth(1.5)
        self.ax_bar.yaxis.set_major_locator(MaxNLocator(integer=True))



class HBarFigure(BarFigure):
    def __init__(self) -> None:
        super().__init__()
    

    def make_bars(self, labels: list[str], groups: list[BarsGroup], width: float, space: float) -> None:
        nlbl = len(labels)
        baseline = np.zeros(nlbl)
        y, ypos, left = self._set_bars(nlbl, len(groups), width, space)
        transform = self.ax_bar.get_yaxis_transform() + ScaledTranslation(-10/72, 0, self.figure.dpi_scale_trans)

        i = 0
        for item in groups:
            values = item.values
            ypos_i = ypos[i, :]
            self._make_bars_level(self.ax_bar.barh, values, item.colors, ypos_i, left[i, :], width)
            self._set_total_values(values, baseline, ypos_i, transform)
            i+=1
        self._set_legend([item.names for item in groups])

        self.ax_bar.set_yticks(y)
        self.ax_bar.set_yticklabels(labels)

        w, h = self.get_size_inches()
        self.set_size_inches(w, max(h, nlbl * 1))
    

    def set_axes(self) -> None:
        super().set_axes()
        self.ax_bar.yaxis.set_inverted(True)        
        self.ax_bar.grid(True, axis='x')
        self.ax_bar.tick_params(axis='x', bottom=False, labelbottom=False)
        self.ax_bar.tick_params(axis='y', width=1.5, pad=20)
        self.ax_bar.spines['left'].set_linewidth(1.5)
        self.ax_bar.xaxis.set_major_locator(MaxNLocator(integer=True))



