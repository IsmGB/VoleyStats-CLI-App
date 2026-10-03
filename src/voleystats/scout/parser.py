import re
import logging
from typing import Any

from voleystats.scout.models import *


logger = logging.getLogger(__name__)


PATTERNS: dict[str, re.Pattern] = {
    'set': re.compile(r"^set\s+(.*)?$", re.IGNORECASE),
    'timeout': re.compile(r"^([*a])?T(.+)?$", re.IGNORECASE),
    'rally': re.compile(r"^(?:(.+)\s+)?([*a])?p(.+)?$", re.IGNORECASE),
    'combo': re.compile(r"^\.(\d{1,2})([BDR])?([#+/=!-])?(.+)?$", re.IGNORECASE),
    'change': re.compile(r"^([*a])?c(\d{1,2}\.\d{1,2}(?:\s+\d{1,2}\.\d{1,2})*)(.+)?$", re.IGNORECASE),
    # 'change': re.compile(r"^([*a])?c(\d{1,2}\.\d{1,2}(?:\s+\d{1,2}\.\d{1,2}){0,7})(.+)?$", re.IGNORECASE),
    'serve': re.compile(r"^([*a])?(\d{1,2})S([HQT])?([156])?(Z[1-9])?(?:[#+/=!-])?(.+)?$", re.IGNORECASE),
    'rotation': re.compile(r"^(?:\*?z([1-6])(?:\s+az([1-6]))?|az([1-6])(?!\s+z[1-6]))(.+)?$", re.IGNORECASE),
    'action': re.compile(r"^([*a])?(\d{1,2})([ABDEF])?([HMNOQTU])?(K[1-9]|X[1-9])?(Z[1-9])?([#+/=!-])?(.+)?$", re.IGNORECASE)
}


class Logger:
    @staticmethod
    def unbound_group(line: int, string: str) -> None:
        logger.warning("Unbound expression at line %d: %r", line, string)
    
    @staticmethod
    def unbound_line(line: int, string: str) -> None:
        logger.warning("Unbound line %d: %r", line, string)
    
    @staticmethod
    def point_not_found(line: int, string: str) -> None:
        logger.critical("Point not found at line: %d: %r", line, string)
    
    @staticmethod
    def serve_not_found(line: int, string: str) -> None:
        logger.warning("Serve not found at line %d: %r", line, string)
    
    @staticmethod
    def reception_not_found(line: int, string: str) -> None:
        logger.warning("Reception not found at line %d: %r", line, string)
    
    @staticmethod
    def unknown_expression(line: int, string: str) -> None:
        logger.warning("Unknown expression at line %d: %r", line, string)
    
    @staticmethod
    def actions_not_found(line: int, string: str) -> None:
        logger.critical("Actions not found at line: %d: %r", line, string)


def search_gameset(string: str) -> str|None:
        if match := PATTERNS['set'].match(string):
            return match.group(1)
        return None


def search_changes(line: int, string: str) -> tuple[TeamEnum, Any]|None:
    if match := PATTERNS['change'].match(string):
        if match.group(3):
            Logger.unbound_group(line, string)
        
        changes = match.group(2).split()
        return (
            TeamEnum(match.group(1) or TeamEnum.HOME),
            [tuple(map(int, c.split('.'))) for c in changes]
        )
    return None


def search_timeout(line: int, string: str) -> TeamEnum|None:
    if match := PATTERNS['timeout'].match(string):
        if match.group(2):
            Logger.unbound_group(line, string)
        return TeamEnum(match.group(1) or TeamEnum.HOME)
    return None


def search_rotation(line: int, string: str) -> tuple[int|None, int|None]|None:
    if match := PATTERNS['rotation'].match(string):
        if match.group(4):
            Logger.unbound_group(line, string)

        home, *away = match.groups()[:-1]
        return (
            None if home is None else int(home),
            (None if away[1] is None else int(away[1])) if away[0] is None else int(away[0])
        )
    return None


def search_rally(line: int, string: str) -> tuple[str, TeamEnum]|None:
    if match := PATTERNS['rally'].match(string):
        if not (actions := match.group(1)):
            Logger.actions_not_found(line, string)
            return None
        if match.group(3):
            Logger.unbound_group(line, string)
        return (actions, TeamEnum(match.group(2) or TeamEnum.HOME))
    return None


def search_actions(line: int, string: str) -> list[Action]:
    rally = []
    if not (actions := string.split()):
        return rally
    
    serve, receive = _search_serve_receive(line, actions[0])
    if serve:
        rally.append(serve)
        if receive:
            rally.append(receive)
        elif serve.value == ValueEnum.ERROR:
            pass
        else:
            Logger.reception_not_found(line, string)
    else:
        Logger.serve_not_found(line, string)

    for action in actions[1:]:
        if (match := PATTERNS['action'].match(action)) is None:
            Logger.unknown_expression(line, string)
            continue
        group = match.groups()
        item = Action(
            team=TeamEnum(group[0] or TeamEnum.HOME),
            player=int(group[1]),
            skill=SkillEnum(group[2] or SkillEnum.ATTACK),
            hit=HitEnum(group[3] or HitEnum.HIGH),
            ext=ExtEnum(group[4]) if group[4] else None,
            zone=ZoneEnum(group[5]) if group[5] else None,
            value=ValueEnum(group[6] or ValueEnum.POSITIVE)
        )
        if group[7] is None:
            rally.append(item)
            continue
        if combo := _search_combo(line=line, string=group[7], prev=item):
            item.value = combo.value.combo(combo.skill)
            rally.extend([item, combo])
    return rally


def _search_serve_receive(line: int, string: str) -> tuple[Action|None, Action|None]:
    if match := PATTERNS['serve'].match(string):
        group = match.groups()
        hit = HitEnum(group[2] or HitEnum.HIGH)
        if (ext := group[3]):
            ext = ExtEnum(f"{'K' if hit == HitEnum.QUICK else 'X'}{ext}")

        serve = Action(
            team=TeamEnum(group[0] or TeamEnum.HOME),
            player=int(group[1]),
            skill=SkillEnum.SERVE,
            hit=hit,
            ext=ext or None,
            zone=ZoneEnum(group[4]) if group[4] else None,
            value=ValueEnum.ERROR
        )
        if group[5] is None:
            return serve, None
        if receive := _search_combo(line=line, string=group[5], prev=serve):
            serve.value = receive.value.combo(receive.skill)
            return serve, receive
    return None, None


def _search_combo(line: int, string: str, prev: Action) -> Action|None:
    if match := PATTERNS['combo'].match(string):
        if match.group(4):
            Logger.unbound_group(line, string)

        return Action(
            team=TeamEnum.HOME if prev.team == TeamEnum.AWAY else TeamEnum.AWAY,
            player=int(match.group(1)),
            skill=SkillEnum(match.group(2) or prev.skill.combo),
            hit=prev.hit,
            ext=prev.ext,
            zone=prev.zone,
            value=ValueEnum(match.group(3) or ValueEnum.POSITIVE)
        )
    return None