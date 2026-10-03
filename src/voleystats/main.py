import click
import json
import logging
from pathlib import Path
from typing import Any, Optional

from voleystats.scout import parser, scout_reader
from voleystats.excel_report import ExcelReport, Sheet, Teams
from voleystats.config import Config

# debug
from voleystats.scout.models import *


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(filename)s: %(message)s"
)
logger = logging.getLogger(__name__)


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
    # voleystats voleystats_example.txt excel_example.xlsx --home cvr_2526.json
    
    # dbug_filename = CODES[int(filename)]
    # dbug_excelfile = EXCEL
    # if dbug_excelfile.exists():
    #     dbug_excelfile.unlink()
    #     print("Debug excel file deleted. :)")
    # players = {
    #     'home': _load_players(PLAYERS['home'])
    # }
    # # config = _load_config(CONFIG)

    scout = scout_reader.ScoutReader()
    with config.input.open(encoding='utf-8') as file:
        linecount = 0
        for string in file:
            linecount += 1
            if not (string := string.strip()):
                continue

            match = parser.search_gameset(string)
            if match is not None:
                gameset = GameSet(name=match)
                scout.add_gameset(gameset)
                continue

            match = parser.search_changes(linecount, string)
            if match is not None:
                team, changes = match
                score = scout.score
                for num_out, num_in in changes:
                    change = Change(team=team, score=score, num_out=num_out, num_in=num_in)
                    scout.add_technical(change)
                continue

            match = parser.search_timeout(linecount, string)
            if match is not None:
                scout.add_technical(Timeout(team=match, score=scout.score))
                continue

            match = parser.search_rotation(linecount, string)
            if match is not None:
                scout.update_rotation(*match)
                continue

            match = parser.search_rally(linecount, string)
            if match is None:
                continue
            if actions := parser.search_actions(linecount, match[0]):
                point = Point(team=match[1], score=scout.score, gameset_id=scout.gameset_id)
                rally = Rally(actions=actions, point=point, rotation=scout.rotation)
                scout.add_rally(rally)
                scout.add_point(point)
            else:
                parser.Logger.actions_not_found(linecount, string)


    with ExcelReport(config.excelfile, scout.asdataframe(), config.team) as excel:
        if (rawfile := config.raw):
            with rawfile.open('w', encoding='utf-8') as f:
                f.write(str(scout))

        excel.build_worksheet_data()
        excel.build_worksheet_data('home')
        excel.build_worksheet_data('away')

        excel.build_worksheet_atack('home')
        excel.build_worksheet_atack('away')

        excel.build_worksheet_serve('home')
        excel.build_worksheet_serve('away')

        excel.build_worksheet_receive('home')
        excel.build_worksheet_receive('away')
        
        # excel.build_worksheet_objetives()
        return




if __name__ == '__main__':
    voleystats()