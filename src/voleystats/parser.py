import re
from pathlib import Path

from typing import Optional

from voleystats.data_classes import *


PATTERNS: dict[str, re.Pattern] = {
    'change': re.compile(r"^([*a])?c\s*((?:\d{1,2}\.\d{1,2}\s+){0,5}\d{1,2}\.\d{1,2})$", re.IGNORECASE),
    'code': re.compile(r"([*a.])?(\d{1,2})([ABDEFRS])?([FMNOU]|K[1-9]|X[1-9]|[HQT][156]?)?(Z[1-9])?([#+/=!-])?", re.IGNORECASE),
    'point': re.compile(r"(?<!\w)([*a])?p$", re.IGNORECASE),
    'rotation': re.compile(r"\b([*a])?z([1-6])\b", re.IGNORECASE),
    'gameset': re.compile(r"^set\s*(.*)?$", re.IGNORECASE),
    'timeout': re.compile(r"^([*a])?t$", re.IGNORECASE)
}


def re_code(line: str) -> list[SingleAction]:
    rally = []
    for nmons in PATTERNS['code'].findall(line):
        item = SingleAction(nmons=nmons)
        if item.team == NmonTeam.COMBO:
            item.complete_as_combo(rally[-1])
            rally[-1].value = VALUES_DICT[item.skill][item.value]
        else:
            item.complete_as_single()
        rally.append(item)
    return rally


def re_gameset(line: str) -> Optional[GameSet]:
        if match := PATTERNS['gameset'].match(line):
            return GameSet(name=match.group(1))
        return None


def re_rotation(line: str) -> Optional[TeamDict[int]]:
    rotation: TeamDict[int] = {}
    for match in PATTERNS['rotation'].finditer(line):
        team = NmonTeam(match.group(1) or NmonTeam.HOME)
        rotation[team] = int(match.group(2))
    
    if rotation:
        return {
            NmonTeam.HOME: rotation.get(NmonTeam.HOME, 0),
            NmonTeam.AWAY: rotation.get(NmonTeam.AWAY, 0)
        }
    return None


def re_point(line: str) -> Optional[NmonTeam]:
    if point:= PATTERNS['point'].search(line):
        return NmonTeam(point.group(1) or NmonTeam.HOME)
    return None


def re_change(line: str) -> Optional[list[Change]]:
    if match:= PATTERNS['change'].match(line):
        team = NmonTeam(match.group(1) or NmonTeam.HOME)
        changes = (m for m in match.group(2).split())
        return [Change(team, *map(int, c.split('.'))) for c in changes]
    return None


def re_timeout(line: str) -> Optional[Timeout]:
    if match := PATTERNS['timeout'].match(line):
        team = NmonTeam(match.group(1) or NmonTeam.HOME)
        return Timeout(team)
    return None