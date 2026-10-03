import unittest
from voleystats.scout import parser
from voleystats.scout.models import *
import re

class TestPatterns(unittest.TestCase):
    def test_change_pattern(self):
        cases = [
            ('z1', None),
            ('c 1.2', None),
            ('c1.2', (None, '1.2', None)),
            ('ac1.2 3.4', ('a', '1.2 3.4', None)),
            ('ac1.2 remain', ('a', '1.2', ' remain')),
            ('c1.2 3.4 5.6 7.8 9.10 11.12 13.14', (None, '1.2 3.4 5.6 7.8 9.10 11.12 13.14', None))
        ]
        self._assertPatterns('change', cases)
    
    def test_rotation_pattern(self):
        cases = [
            ('jz1', None),
            ('az6 z1', None),
            ('z1', ('1', None, None, None)),
            ('az1', (None, None, '1', None)),
            ('z6 az1', ('6', '1', None, None)),
            ('*z1 remain', ('1', None, None, ' remain')),
            ('az1 remain', (None, None, '1', ' remain'))
        ]
        self._assertPatterns('rotation', cases)
    
    def test_combo_pattern(self):
        cases = [
            ('.10#', ('10', None, '#', None)),
            ('.10#remain', ('10', None, '#', 'remain')),
        ]
        self._assertPatterns('combo', cases)
    
    def test_action_pattern(self):
        cases = [
            ('a3=', ('a', '3', None, None, None, None, '=', None))
        ]
        self._assertPatterns('action', cases)
    
    def test_serve_pattern(self):
        cases = [
            ('a33SQ1Z1=', ('a', '33', 'Q', '1', 'Z1', None))
        ]
        self._assertPatterns("serve", cases)
    
    def test_rally_pattern(self):
        cases = [
            ('asdf p', ('asdf', None, None)),
            ('p', (None, None, None)),
            ('asdasd', None)
        ]
        self._assertPatterns('rally', cases)

    def _assertPatterns(self, key: str, test_cases: list[tuple[str, tuple[str|None, ...]]]):
        pattern = parser.PATTERNS[key]
        for test, expected in test_cases:
            with self.subTest(test=test):
                groups = match.groups() if (match := pattern.match(test)) else match
                self.assertEqual(groups, expected)



class TestReportUnbound(unittest.TestCase):
    def test_logger(self):
        with self.assertLogs() as logs:
            test = parser.Logger.unbound_group(0, "expression")
        self.assertIsNone(test)
        self.assertEqual(logs.records[0].message, "Unbound expression at line 0: 'expression'")



class TestSearchChanges(unittest.TestCase):
    def test_zero_changes(self):
        self.assertIsNone(parser.search_changes(0, "ac"))
    
    def test_one_change(self):
        self.assertEqual(parser.search_changes(0, "c1.2"), (TeamEnum.HOME, [(1, 2)]))
    
    def test_two_changes(self):
        self.assertEqual(parser.search_changes(0, "c1.2 3.4"), (TeamEnum.HOME, [(1, 2), (3, 4)]))

    def test_remain(self):
        with self.assertLogs() as logs:
            self.assertEqual(parser.search_changes(0, 'c1.2 remain'), (TeamEnum.HOME, [(1, 2)]))
            self.assertEqual(len(logs.output), 1)


class TestSearchTimeout(unittest.TestCase):
    def test_timeout_home(self):
        self.assertEqual(parser.search_timeout(0, "*T"), TeamEnum.HOME)
    
    def test_timeout_away(self):
        self.assertEqual(parser.search_timeout(0, "aT"), TeamEnum.AWAY)
    
    def test_timeout_other(self):
        with self.assertLogs() as logs:
            self.assertEqual(parser.search_timeout(0, '*T remain'), TeamEnum.HOME)
            self.assertEqual(len(logs.output), 1)



class TestSearchGameset(unittest.TestCase):
    def test_match_gameset(self):
        self.assertEqual(parser.search_gameset("set name"), "name")
    
    def test_not_match_gameset(self):
        self.assertIsNone(parser.search_gameset("There is no set here."))



class TestSearchRotation(unittest.TestCase):    
    def test_rotate_home(self):
        self.assertEqual(parser.search_rotation(0, "z1"), (1, None))
    
    def test_rotate_away_isolated(self):
        self.assertEqual(parser.search_rotation(0, "az1"), (None, 1))
    
    def test_rotate_both(self):
        self.assertEqual(parser.search_rotation(0, "z6 az1"), (6, 1))
    
    def test_rotate_inverted(self):
        self.assertIsNone(parser.search_rotation(0, "az6 z1"))
    
    def test_rotate_reamain(self):
        with self.assertLogs() as logs:
            self.assertEqual(parser.search_rotation(0, "az1 remain"), (None, 1))
            self.assertEqual(len(logs.output), 1)



class TestSearchCombo(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.prev = Action(
            team=TeamEnum.HOME,
            player=6,
            skill=SkillEnum.ATTACK,
            hit=HitEnum.QUICK,
            ext=ExtEnum.K1,
            zone=ZoneEnum.Z5,
            value=ValueEnum.ERROR
        )

    def test_combo_not_found(self):
        self.assertIsNone(parser._search_combo(0, "10#", self.prev))
    
    def test_combo_remain(self):
        expected = Action(
            team=TeamEnum.AWAY,
            player=10,
            skill=SkillEnum.BLOCK,
            hit=HitEnum.QUICK,
            ext=ExtEnum.K1,
            zone=ZoneEnum.Z5,
            value=ValueEnum.PERFECT
        )
        with self.assertLogs() as logs:
            self.assertEqual(parser._search_combo(0, ".10#remain", self.prev), expected)
            self.assertEqual(len(logs.output), 1)



class TestSearchServeReceive(unittest.TestCase):
    def test_serve_not_found(self):
        self.assertEqual(parser._search_serve_receive(0, "6Q="), (None, None))

    def test_match_serve(self):
        expected = Action(
            team=TeamEnum.HOME,
            player=6,
            skill=SkillEnum.SERVE,
            hit=HitEnum.QUICK,
            ext=None,
            zone=None,
            value=ValueEnum.ERROR
        )
        self.assertEqual(parser._search_serve_receive(0, "6SQ="), (expected, None))
    
    def test_match_serve_receive(self):
        serve = Action(
            team=TeamEnum.HOME,
            player=6,
            skill=SkillEnum.SERVE,
            hit=HitEnum.QUICK,
            ext=ExtEnum.K5,
            zone=ZoneEnum.Z1,
            value=ValueEnum.NEGATIVE
        )
        receive = Action(
            team=TeamEnum.AWAY,
            player=8,
            skill=SkillEnum.RECEIVE,
            hit=HitEnum.QUICK,
            ext=ExtEnum.K5,
            zone=ZoneEnum.Z1,
            value=ValueEnum.PERFECT
        )
        self.assertEqual(parser._search_serve_receive(0, "6SQ5Z1.8#"), (serve, receive))



class TestSearchActions(unittest.TestCase):
    def test_empty_input(self):
        self.assertListEqual(parser.search_actions(0, ""), [])
    
    def test_missing_serve(self):
        expected = [
            Action(
                team=TeamEnum.AWAY,
                player=3,
                skill=SkillEnum.ATTACK,
                hit=HitEnum.HIGH,
                ext=None,
                zone=None,
                value=ValueEnum.ERROR
            )
        ]
        with self.assertLogs() as logs:
            self.assertListEqual(parser.search_actions(0, "6Q.8- a3="), expected)
            self.assertEqual(len(logs.output), 1)
    
    def test_actions_with_combo(self):
        expected = [
            Action(
                team=TeamEnum.HOME,
                player=6,
                skill=SkillEnum.SERVE,
                hit=HitEnum.QUICK,
                ext=None,
                zone=None,
                value=ValueEnum.POSITIVE
            ),
            Action(
                team=TeamEnum.AWAY,
                player=8,
                skill=SkillEnum.RECEIVE,
                hit=HitEnum.QUICK,
                ext=None,
                zone=None,
                value=ValueEnum.NEGATIVE
            ),
            Action(
                team=TeamEnum.AWAY,
                player=3,
                skill=SkillEnum.ATTACK,
                hit=HitEnum.HIGH,
                ext=None,
                zone=None,
                value=ValueEnum.SLASH
            ),
            Action(
                team=TeamEnum.HOME,
                player=2,
                skill=SkillEnum.BLOCK,
                hit=HitEnum.HIGH,
                ext=None,
                zone=None,
                value=ValueEnum.PERFECT
            )
        ]
        self.assertListEqual(parser.search_actions(0, "6SQ.8- a3.2#"), expected)