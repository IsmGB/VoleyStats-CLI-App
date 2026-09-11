import click
import json
from pathlib import Path

from voleystats import parser, stats_manager, graphs
from voleystats.excel_report import ExcelReport, Sheet, Teams
from voleystats.config import Config

# debug
from voleystats.data_classes import *
from random import choice


ROOT = Path(__file__).resolve().parents[2]
TMP = ROOT / "tmp"

CODES = (
    TMP / "match_test.txt",
    TMP / "pachanga_2026-06-30.txt",
    TMP / "CVR_Servet_20260328.txt"
)
PLAYERS = {
    'home': TMP / "cvr_2526.json",
    'away': None
}
EXCEL = TMP / "excel_test.xlsx"
CONFIG = Path(__file__).resolve().parent / "config.json"


def _load_players(jsonfile: Path) -> dict[int, dict[str, str]]|None:
    if jsonfile.exists():
        with jsonfile.open(encoding='utf-8') as f:
            return {int(n): value for n, value in json.load(f).items()}


def _load_config(jsonfile: Path) -> Any:
    if jsonfile.exists():
        with jsonfile.open(encoding='utf-8') as f:
            return json.load(f)


@click.command()
@click.argument("filename", type=str)
@click.argument("excelfile", type=str, default='')
@click.option("--raw", type=str)
@click.option("--home", type=str)
@click.option("--away", type=str)
@click.option("--configfile", type=str)
def voleystats(filename: str, excelfile: str, raw: Optional[str], home: Optional[str], away: Optional[str], configfile: Optional[str]) -> None:
    config = Config(filename, excelfile, configfile)

    if home:
        config.load_team('home', Path(home))
    if away:
        config.load_team('away', Path(away))
    if raw:
        config.set_raw(Path(raw))


    # DEBUG
    # dbug_filename = CODES[int(filename)]
    # dbug_excelfile = EXCEL
    # if dbug_excelfile.exists():
    #     dbug_excelfile.unlink()
    #     print("Debug excel file deleted. :)")
    # players = {
    #     'home': _load_players(PLAYERS['home'])
    # }
    # # config = _load_config(CONFIG)

    manager = stats_manager.StatsManager()
    with config.input.open('r', encoding='utf-8') as f:
        for line in f.read().split("\n"):
            gameset = parser.re_gameset(line)
            if gameset is not None:
                manager.add_gameset(gameset)
                continue

            change = parser.re_change(line)
            if change is not None:
                for c in change:
                    manager.add_event(c)
                continue

            timeout = parser.re_timeout(line)
            if timeout is not None:
                manager.add_event(timeout)
                continue

            rotation = parser.re_rotation(line)
            if rotation is not None:
                manager.set_rotation(rotation)
                continue
            
            manager.add_codes(parser.re_code(line))
            
            point = parser.re_point(line)
            if point is not None:
                manager.add_point(point)
    
    with ExcelReport(config.excelfile, manager.asdataframe(), config.team) as excel:
        if (rawfile := config.raw):
            with rawfile.open('w', encoding='utf-8') as f:
                f.write(str(manager))

        excel.build_worksheet_data()
        excel.build_worksheet_data('home')
        excel.build_worksheet_data('away')

        # excel.build_worksheet_atack('home')
        # excel.build_worksheet_atack('away')

        # excel.build_worksheet_serve('home')
        # excel.build_worksheet_serve('away')

        # excel.build_worksheet_receive('home')
        # excel.build_worksheet_receive('away')
        
        excel.build_worksheet_objetives()
        return

        # for item in excel.counts:
        #     print(item)

        # fig = graphs.CourtPlot("Distribución de ataque")
        # # for e in list(NmonHit):
        # #     fig.plot_marker(e, NmonExt.NONE, choice(list(NmonZone)[:-1]))
        # for e in list(NmonExt)[:-1]:
        #     fig.plot_marker(NmonHit.HIGH, e, choice(list(NmonZone)[:-1]))
        # # fig.plot()
        # # fig.savefig(TMP/"test_fig.png")
        # excel.insert_chart(fig.savefig_bytes())




if __name__ == '__main__':
    voleystats()