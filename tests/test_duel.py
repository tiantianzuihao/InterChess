import unittest
from unittest.mock import patch
import chess
import duel

class DuelTests(unittest.TestCase):
    def tearDown(self): duel.GAMES.clear()
    def game(self, human=True, minutes=0, increment=0):
        game=duel.Game(1,'white' if human else 'black',minutes,increment)
        duel.GAMES['test']=game
        return game
    def call(self, action, **kwargs): return duel.handle({'id':'test','action':action,**kwargs})
    def test_moves_and_turn_guard(self):
        g=self.game();r=self.call('move',move='e2e4')
        self.assertEqual(r['turn'],'black')
        self.assertEqual(r['move_details'][0]['piece'],'P')
        with self.assertRaises(ValueError): self.call('move',move='d2d4')
        self.assertEqual(len(g.board.move_stack),1)
    def test_clock_increment_and_poll(self):
        with patch('duel.time.monotonic',return_value=100):g=self.game(minutes=1,increment=3)
        with patch('duel.time.monotonic',return_value=105):r=self.call('move',move='e2e4')
        self.assertEqual(r['clocks'],{'white':58,'black':60})
        with patch('duel.time.monotonic',return_value=112):r=self.call('state')
        self.assertEqual(r['clocks'],{'white':58,'black':53})
    def test_timeout_and_insufficient_material(self):
        with patch('duel.time.monotonic',return_value=0):g=self.game(minutes=1)
        with patch('duel.time.monotonic',return_value=61):r=self.call('move',move='e2e4')
        self.assertEqual(r['result']['winner'],'black');self.assertEqual(r['history'],[])
        with patch('duel.time.monotonic',return_value=0):g=self.game(minutes=1)
        g.board=chess.Board('7k/8/8/8/8/8/8/R3K3 w Q - 0 1')
        with patch('duel.time.monotonic',return_value=61):r=self.call('state')
        self.assertIsNone(r['result']['winner'])
    def test_mate_and_resign(self):
        g=self.game()
        for uci in ['f2f3','e7e5','g2g4','d8h4']:g.push(chess.Move.from_uci(uci))
        self.assertEqual(g.result,{'winner':'black','reason':'将死'})
        self.game(False);self.assertEqual(self.call('resign')['result']['winner'],'white')
    def test_special_moves(self):
        g=self.game();g.board=chess.Board('4k3/P7/8/8/8/8/8/4K3 w - - 0 1')
        r=self.call('move',move='a7a8n');self.assertEqual(r['pieces']['a8'],'N')
        g=self.game();g.board=chess.Board('4k3/8/8/8/8/8/8/4K2R w K - 0 1')
        r=self.call('move',move='e1g1');self.assertEqual(r['pieces']['f1'],'R')
    def test_settings(self):
        for level in [0,9,True]:
            with self.assertRaises(ValueError):duel.handle({'action':'new','level':level,'color':'white'})
        with patch('duel.get_engine'):
            r=duel.handle({'action':'new','level':8,'color':'black','minutes':5,'increment':3})
        self.assertEqual(r['human'],'black');self.assertEqual(r['clocks']['white'],300)
