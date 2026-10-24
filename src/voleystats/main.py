import click
import json
import logging
from pathlib import Path
from copy import copy
from typing import Any, Optional, cast

from voleystats.scout import parser, scout_reader
from voleystats.analysis.excel_report import ExcelReport
from voleystats.analysis.validation import *

# debug
from voleystats.scout.models import *


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s %(levelname)s] %(filename)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


@click.command()
@click.argument("filename", type=str)
@click.argument("excelfile", type=str, default="")
@click.option("--raw", type=str)
@click.option("--home", type=str)
@click.option("--away", type=str)
@click.option("--configfile", type=str)
def voleystats(filename: str, excelfile: str, raw: Optional[str], home: str|None, away: str|None, configfile: Optional[str]) -> None:
    scout = scout_reader.ScoutReader()
    with Path(filename).open(encoding='utf-8') as file:
        logger.info("Start pasing.")
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
                rally = Rally(actions=actions, point=point, rotation=copy(scout.rotation))
                scout.add_rally(rally)
                scout.add_point(point)
            else:
                parser.Logger.actions_not_found(linecount, string)
        logger.info("Parsing completed.")

    teams: dict[TeamKey, Team] = {
        'home': load_team_from_json(home),
        'away': load_team_from_json(away)
    }

    with ExcelReport(Path(excelfile), scout.asdataframe(), teams) as excel:
        logger.info("Start writing.")
        excel.build_sheet_main()
        logger.info("MAIN completed.")

        excel.build_sheet_team('home')
        excel.build_sheet_team('away')
        logger.info("TEAMS completed.")

        excel.build_sheet_attack('home')
        excel.build_sheet_attack('away')
        logger.info("ATTACK completed.")

        excel.build_sheet_serve('home')
        excel.build_sheet_serve('away')
        logger.info("SERVE completed.")

        excel.build_sheet_receive('home')
        excel.build_sheet_receive('away')
        logger.info("RECEIVE completed.")
        
        # excel.build_worksheet_objetives()
        return




if __name__ == '__main__':
    # voleystats()
    voleystats.main(args=["tmp/hlp_granavoley_2026-10-03.txt", "test.xlsx", "--home", "saves/teams/lp_2627.json"], standalone_mode=False)