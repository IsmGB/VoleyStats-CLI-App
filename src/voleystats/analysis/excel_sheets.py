import xlsxwriter as xlsx
from xlsxwriter.workbook import Format
from pandas._typing import Scalar
from abc import ABC, abstractmethod
from io import BytesIO
from dataclasses import dataclass, field
from typing import TypeVar, Any, TypedDict, NotRequired

from voleystats.enums import TeamKey, TeamsDict, ValueEnum
# from voleystats.analysis.sheet_adapter import *



@dataclass(slots=True)
class Container:
    data: dict
    charts: dict = field(default_factory=dict)


class Sheet(ABC):
    HEADER = ['Tot.', '%Eff.', *[x for v in list(ValueEnum) for x in (v, f"%{v}")]]

    def __init__(self, name: str, workbook: xlsx.Workbook, contents: Container, formats: SheetFormats) -> None:
        self.worksheet = workbook.add_worksheet(name)
        self.contents = contents
        self.formats = formats
    

    def write_header(self, row: int, col: int, data: list[str], cell_format: Format|None = None) -> None:
        self.worksheet.write_row(row, col, data, cell_format)
        try:
            idx = data.index('=')
            self.worksheet.write_string(row, col+idx, '=', cell_format)
        except ValueError:
            return
    

    def fit_column(self, col: int, data: list[Any], min_width: int = 8) -> None:
        width = max(max(len(str(item)) for item in data), min_width) if data else min_width
        self.worksheet.set_column(col, col, width=width)


    def merge_range(
        self,
        start: tuple[int, int],
        end: tuple[int, int],
        data: Any,
        frmt_merge: Format|None=None,
        frmt_write: Format|None=None
    ) -> None:
        if start == end:
            self.worksheet.write(*start, data, frmt_write)
        else:
            self.worksheet.merge_range(*start, *end, data, frmt_merge)
    

    def insert_image(self, row: int, col: int, img_bytes: BytesIO, opts: dict) -> None:
        img_bytes.seek(0)
        self.worksheet.insert_image(row, col, img_bytes, opts)
    

    def set_percent_columns(self, col: int, first_row: int, last_row: int, idx: int, bold: bool=False) -> None:
        n_cols = col + 13 # 7 cols: [Eff, #, +, !, -, /, =]
        even_cond = f"=MOD(ROW()-{idx},2)=0"
        odd_cond = f"=MOD(ROW()-{idx},2)=1"
        frmt_even, frmt_odd = self.formats.percent_bold if bold else self.formats.percent

        for c in range(col, n_cols, 2):
            self.worksheet.conditional_format(
                first_row=first_row, first_col=c,
                last_row=last_row, last_col=c,
                options={'type': 'formula', 'criteria': even_cond, 'format': frmt_even}
            )
            self.worksheet.conditional_format(
                first_row=first_row, first_col=c,
                last_row=last_row, last_col=c,
                options={'type': 'formula', 'criteria': odd_cond, 'format': frmt_odd}
            )
    
    @staticmethod
    def _rm_zeros(values: list) -> list:
        return [v or '' for v in values]





class MainSheet(Sheet):
    def __init__(self, name: str, workbook: xlsx.Workbook, contents: Container, formats: SheetFormats) -> None:
        super().__init__(name, workbook, contents, formats)

        self.row = 0
        self.fit_column(0, [])
        self.write_table(0, 0, 'home')
        self.write_table(self.row + 1, 0, 'away')
        self.insert_image(1, 18, self.contents.charts['pts'], {})

    
    def write_table(self, row: int, col: int, team: TeamKey):
        contents = self.contents.data[team].data
        fdata = self.formats.data
        fdata_bold = self.formats.data_bold
        fmerge = self.formats.merge
        # Header
        self.write_header(row, col, ['Team', 'Set', 'Skill', *self.HEADER], self.formats.header)
        row += 1
        # Skills by set
        row0 = row
        merge_idx = 1
        for s, skills in contents['eff'].items():
            start = row
            for values in skills:
                idx = (row - row0 + 1) % 2
                self.worksheet.write_row(row, col+2, self._rm_zeros(values), fdata[idx%2])
                row += 1
            self.merge_range((start, col+1), (row-1, col+1), s, fmerge[merge_idx%2], fdata[merge_idx%2])
            merge_idx += 1
        self.set_percent_columns(col+4, row0, row-1, row0)
        # Total skill
        start = row
        for values in contents['total']:
            idx = (row - row0 + 1) % 2
            self.worksheet.write_row(row, col+2, self._rm_zeros(values), fdata_bold[idx%2])
            row += 1
        self.merge_range((start, col+1), (row-1, col+1), 'TOTAL', self.formats.merge_bold[merge_idx%2], fdata_bold[merge_idx%2])
        self.set_percent_columns(col+4, start, row-1, row0, bold=True)
        # Team name
        self.merge_range((row0, col), (row-1, col), team.capitalize(), fmerge[1], fdata[1])
        self.row = row



class TeamsSheet(Sheet):
    def __init__(self, name: str, workbook: xlsx.Workbook, contents: Container, formats: SheetFormats) -> None:
        super().__init__(name, workbook, contents, formats)

        self.row = 0
        self.fit_column(0, [cnt.data['name'] for cnt in self.contents.data.values()])
        for n in self.contents.data.keys():
            self.write_table(self.row, 0, n)
            self.row += 1
        self.insert_image(1, 18, self.contents.charts['pts'], {})
    

    def write_table(self, row: int, col: int, player: int) -> None:
        contents = self.contents.data[player].data
        fdata = self.formats.data
        fdata_bold = self.formats.data_bold
        fmerge = self.formats.merge
        # Header
        self.write_header(row, col, ['Player', 'Set', 'Skill', *self.HEADER], self.formats.header)
        row += 1
        # Skills by set
        row0 = row
        merge_idx = 1
        for s, skills in contents['eff'].items():
            start = row
            for values in skills:
                idx = (row - row0 + 1) % 2
                self.worksheet.write_row(row, col+2, self._rm_zeros(values), fdata[idx%2])
                row += 1
            self.merge_range((start, col+1), (row-1, col+1), s, fmerge[merge_idx%2], fdata[merge_idx%2])
            merge_idx += 1
        self.set_percent_columns(col+4, row0, row-1, row0)
        # Total skill
        start = row
        for values in contents['total']:
            idx = (row - row0 + 1) % 2
            self.worksheet.write_row(row, col+2, self._rm_zeros(values), fdata_bold[idx%2])
            row += 1
        self.merge_range((start, col+1), (row-1, col+1), 'TOTAL', self.formats.merge_bold[merge_idx%2], fdata_bold[merge_idx%2])
        self.set_percent_columns(col+4, start, row-1, row0, bold=True)
        # Player name
        self.merge_range((row0, col), (row-1, col), contents['name'], fmerge[1], fdata[1])
        self.row = row




class AttackSheet(Sheet):
    def __init__(self, name: str, workbook: xlsx.Workbook, contents: Container, formats: SheetFormats) -> None:
        super().__init__(name, workbook, contents, formats)

        self.row = 0
        self.fit_column(0, [cnt.data['name'] for cnt in self.contents.data.values()])
        for n, cnt in self.contents.data.items():
            self.write_table(self.row, 0, n)
            self.row += 1

            charts = cnt.charts
            if (pie := charts.get('pie')) is None:
                continue
            self.insert_image(self.row, 0, pie, {'x_scale': 0.9, 'y_scale': 0.9, 'x_offset': 10})

            net_col = 5
            for court in charts['courts']:
                self.insert_image(self.row, net_col, court, {'x_scale': 0.85, 'y_scale': 0.85})
                net_col += 13
            self.row += 16

    
    def write_table(self, row: int, col: int, player: int) -> None:
        contents = self.contents.data[player].data
        fdata = self.formats.data
        fdata_bold = self.formats.data_bold
        fmerge = self.formats.merge
        # Header
        self.write_header(row, col, ['Player', 'Hit', 'Ext.', *self.HEADER], self.formats.header)
        row += 1
        # Skills by set
        row0 = row
        for values in contents['eff']:
            idx = (row - row0 + 1) % 2
            self.worksheet.write_row(row, col+1, self._rm_zeros(values), fdata[idx])
            row += 1
        self.set_percent_columns(col+4, row0, row-1, row0)
        # Total skill
        idx = (row - row0 + 1) % 2
        self.merge_range((row, col+1), (row, col+2), 'TOTAL', self.formats.merge_bold[idx], fdata_bold[idx])
        self.worksheet.write_row(row, col+3, self._rm_zeros(contents['total']), fdata_bold[idx])
        self.set_percent_columns(col+4, row, row, row0, bold=True)
        row += 1
        # Player name
        self.merge_range((row0, col), (row-1, col), contents['name'], fmerge[1], fdata[1])
        self.row = row



class ServeSheet(Sheet):
    def __init__(self, name: str, workbook: xlsx.Workbook, contents: Container, formats: SheetFormats) -> None:
        super().__init__(name, workbook, contents, formats)

        self.row = 0
        self.fit_column(0, [cnt.data['name'] for cnt in self.contents.data.values()])
        for n, cnt in self.contents.data.items():
            self.write_table(self.row, 0, n)
            self.row += 1

            charts = cnt.charts
            if (pie := charts.get('pie')) is None:
                continue
            self.insert_image(self.row, 0, pie, {'x_scale': 0.9, 'y_scale': 0.9, 'x_offset': 10})

            net_col = 5
            for chart in charts.get('hit_pies', []):
                self.insert_image(self.row, net_col, chart, {'x_scale': 0.9, 'y_scale': 0.9})
                net_col += 7
            self.row += 16
    

    def write_table(self, row: int, col: int, player: int) -> None:
        contents = self.contents.data[player].data
        fdata = self.formats.data
        fdata_bold = self.formats.data_bold
        fmerge = self.formats.merge
        # Header
        self.write_header(row, col, ['Player', 'Hit', 'Ext.', *self.HEADER], self.formats.header)
        row += 1

        row0 = row
        merge_idx = 1
        for values in contents['eff']:
            idx = (row - row0 + 1) % 2
            self.worksheet.write_row(row, col+1, self._rm_zeros(values), fdata[idx])
            row += 1
        self.set_percent_columns(col+4, row0, row-1, row0)
        idx = (row - row0 + 1) % 2
        self.merge_range((row, col+1), (row, col+2), 'TOTAL', self.formats.merge_bold[idx], fdata_bold[idx])
        self.worksheet.write_row(row, col+3, self._rm_zeros(contents['total']), fdata_bold[idx])
        self.set_percent_columns(col+4, row, row, row0, bold=True)
        row += 1
        # Player name
        self.merge_range((row0, col), (row-1, col), contents['name'], fmerge[1], fdata[1])
        self.row = row



class ReceiveSheet(Sheet):
    def __init__(self, name: str, workbook: xlsx.Workbook, contents: Container, formats: SheetFormats) -> None:
        super().__init__(name, workbook, contents, formats)

        self.row = 0
        self.fit_column(0, [cnt.data['name'] for cnt in self.contents.data.values()])
        for n, cnt  in self.contents.data.items():
            self.write_table(self.row, 0, n)
            self.row += 1

            charts = cnt.charts
            if (pie := charts.get('pie')) is None:
                continue
            self.insert_image(self.row, 0, pie, {'x_scale': 0.9, 'y_scale': 0.9, 'x_offset': 10})

            net_col = 5
            for chart in charts.get('rot_pies', []):
                self.insert_image(self.row, net_col, chart, {'x_scale': 0.9, 'y_scale': 0.9})
                net_col += 7
            
            if (bar := charts.get('bar')) is not None:
                self.insert_image(self.row, net_col, bar, {'x_scale': 0.8, 'y_scale': 0.8})
                self.row += 18
            
            if (zones := charts.get('zones')) is not None:
                net_col = 0
                for zone in zones:
                    self.insert_image(self.row, net_col, zone, {'x_scale': 0.9, 'y_scale': 0.95, 'x_offset': 10})
                    net_col += 6
                self.row += 16
    

    def write_table(self, row: int, col: int, player: int) -> None:
        contents = self.contents.data[player].data
        fdata = self.formats.data
        fdata_bold = self.formats.data_bold
        fmerge = self.formats.merge
        # Header
        self.write_header(row, col, ['Player', 'Hit', 'Rot.', *self.HEADER], self.formats.header)
        row += 1

        row0 = row
        merge_idx = 1
        for hit, rots in contents['eff'].items():
            start = row
            for values in rots['rotations']:
                idx = (row - row0 + 1) % 2
                self.worksheet.write_row(row, col+2, self._rm_zeros(values), fdata[idx])
                row += 1
            idx = (row - row0 + 1) % 2
            self.worksheet.write_row(row, col+2, ['TOTAL', *self._rm_zeros(rots['total'])], fdata_bold[idx])
            row += 1
            self.merge_range((start, col+1), (row-1, col+1), hit, fmerge[merge_idx%2], fdata[merge_idx%2])
            merge_idx += 1
        self.set_percent_columns(col+4, row0, row-1, row0)
        # Total rotations
        start = row
        for values in contents['total']['rotations']:
            idx = (row - row0 + 1) % 2
            self.worksheet.write_row(row, col+2, self._rm_zeros(values), fdata_bold[idx%2])
            row += 1
        idx = (row - row0 + 1) % 2
        self.worksheet.write_row(row, col+2, ['TOTAL', *contents['total']['total']], fdata_bold[idx])
        row += 1
        self.merge_range((start, col+1), (row-1, col+1), 'TOTAL', self.formats.merge_bold[merge_idx%2], fdata_bold[merge_idx%2])
        self.set_percent_columns(col+4, start, row-1, row0, bold=True)
        # Player name
        self.merge_range((row0, col), (row-1, col), contents['name'], fmerge[1], fdata[1])
        self.row = row


class SheetFormats:
    def __init__(self, workbook: xlsx.Workbook) -> None:
        self.data = (
            workbook.add_format({'bg_color': "#BFDCF1", 'border': 1}),
            workbook.add_format({'bg_color': "#81C3F1", 'border': 1})
        )
        self.merge = (
            workbook.add_format({'bg_color': "#BFDCF1", 'border': 1, 'valign': 'top'}),
            workbook.add_format({'bg_color': "#81C3F1", 'border': 1, 'valign': 'top'}),
        )
        self.percent = (
            workbook.add_format({'bg_color': "#BFDCF1", 'border': 1, 'num_format': "0.0%"}),
            workbook.add_format({'bg_color': "#81C3F1", 'border': 1, 'num_format': "0.0%"}),
        )
        self.header = workbook.add_format(
            {
                'bold': True,
                'font_size': 12,
                'font_color': '#ffffff',
                'bg_color': '#0070C0',
                'border': 1,
                'num_format': '@'
            }
        )
        self.blank = workbook.add_format({'bg_color': '#ffffff'})
        self.data_bold = (
            workbook.add_format({'bg_color': "#BFDCF1", 'border': 1, 'bold': True}),
            workbook.add_format({'bg_color': "#81C3F1", 'border': 1, 'bold': True})
        )
        self.merge_bold = (
            workbook.add_format({'bg_color': "#BFDCF1", 'border': 1, 'valign': 'top', 'bold': True}),
            workbook.add_format({'bg_color': "#81C3F1", 'border': 1, 'valign': 'top', 'bold': True}),
        )
        self.percent_bold = (
            workbook.add_format({'bg_color': "#BFDCF1", 'border': 1, 'num_format': "0.0%", 'bold': True}),
            workbook.add_format({'bg_color': "#81C3F1", 'border': 1, 'num_format': "0.0%", 'bold': True}),
        )
