import unittest
from voleystats.scout.scout_reader import ScoutReader

from voleystats.scout.models import *


class TestScoutReader(unittest.TestCase):

    def setUp(self) -> None:
        self.scout = ScoutReader()
    
    def tearDown(self) -> None:
        del self.scout

    def test_update_rotation(self):
        self.scout.update_rotation(home=2, away=5)
        self.assertEqual(self.scout.rotation, Rotation(2, 5))
        self.assertEqual(str(self.scout), '*z2 az5')
    
    def test_add_gameset(self):
        self.scout.add_gameset(GameSet(name="name"))
        self.assertEqual(self.scout.gameset_id, 1)
        self.assertTupleEqual(self.scout.score, (0, 0))
        self.assertEqual(str(self.scout), "-"*37 + '\nSET (1): name\n' + "-"*37)
    
    def test_add_changes(self):
        change = Change(
            team=TeamEnum.HOME,
            score=(15, 15),
            num_out=6,
            num_in=2
        )
        self.scout.add_technical(change)
        self.assertEqual(str(self.scout), '*c06:02')
    
    def test_add_timeout(self):
        timeout = Timeout(
            team=TeamEnum.HOME,
            score=(15, 15)
        )
        self.scout.add_technical(timeout)
        self.assertEqual(str(self.scout), '*T')
    
    def test_add_point(self):
        pass