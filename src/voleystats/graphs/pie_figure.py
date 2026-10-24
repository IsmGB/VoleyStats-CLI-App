from voleystats.colors import Colors
from .base_figure import *


class PieFigure(BaseFigure):
    def __init__(self) -> None:
        super().__init__(figsize=(4, 4))
        self.ax_pie = self.add_subplot()
    

    def _remove_zeros(self, values: list[float], labels: list[str], colors: list[str]) -> tuple:
        grps = [(v,l,c) for v,l,c in zip(values, labels, colors) if v!=0]
        return ([], [], []) if not grps else tuple(list(grp) for grp in zip(*grps))
    
    
    def make_pie(self, values: list, labels: list, colors: list[str], show_num: bool=True) -> None:
        if (n := len(values)) != len(labels) or n != len(colors):
            raise ValueError("Values, labels and colors must have same length.")
        
        values, labels, colors = self._remove_zeros(values, labels, colors)
        autopct = lambda pct: f"{round(pct*sum(values)/100)} ({pct:.1f}%)" if show_num else '%1.1f%%'

        pie = self.ax_pie.pie(
            x=values, labels=labels, autopct=autopct, wedgeprops={'ec': Colors.WHITE}, colors=colors
        )
        for pct in pie[2]:
            pct.set_fontsize(9)
            pct.set_fontweight('bold')
    

    def set_title(self, title: str) -> None:
        self.ax_pie.set_title(title)
    

    def clear_axes(self) -> None:
        self.ax_pie.clear()