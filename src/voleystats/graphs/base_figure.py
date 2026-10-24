import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from io import BytesIO
from pathlib import Path
from enum import StrEnum
from abc import ABC, abstractmethod



class BaseFigure(Figure, ABC):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.patch.set_edgecolor('black')
        self.patch.set_linewidth(3)

    @abstractmethod
    def clear_axes(self) -> None:
        pass

    def save_bytes(self) -> BytesIO:
        img = BytesIO()
        self.savefig(img, format='png', bbox_inches='tight')
        plt.close(self)
        return img
    
    def save_image(self, path: Path) -> None:
        self.savefig(path)
        plt.close(self)