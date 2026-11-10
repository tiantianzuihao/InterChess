import unittest

import chess
import practice


class ChapterEightTests(unittest.TestCase):
    def test_photos_answers_and_symbols(self):
        data = practice.chapter(8)
        self.assertEqual(sum(p['points'] for p in data['puzzles']), 138)
        self.assertEqual([p['number'] for p in data['puzzles']], list(range(385, 433)))
        self.assertIn(8, [c['number'] for c in practice.catalog()])
        for p in data['puzzles']:
            self.assertTrue(chess.Board(p['fen']).is_valid(), p['number'])
            for line in p['book_lines']:
                board = chess.Board(p['fen'])
                self.assertEqual(len(line['uci']), len(line['san']))
                for uci, san, raw in zip(line['uci'], line['san'], line['transcribed_notation'].split()):
                    move = chess.Move.from_uci(uci)
                    self.assertIn(move, board.legal_moves, p['number'])
                    self.assertEqual(board.san(move), san, p['number'])
                    board.push(move)
                    token = raw.rstrip('!?')
                    if token.endswith('#'):
                        self.assertTrue(board.is_checkmate(), p['number'])
                    elif token.endswith('++'):
                        self.assertGreaterEqual(len(board.checkers()), 2, p['number'])
                    elif token.endswith('+'):
                        self.assertTrue(board.is_check(), p['number'])
                self.assertEqual(board.is_checkmate(), line['ends_in_checkmate'])

    def test_all_main_lines_in_practice(self):
        for p in practice.chapter(8)['puzzles']:
            history = []
            line = p['book_lines'][0]['uci']
            while len(history) < len(line):
                state = practice.play(dict(chapter=8, number=p['number'], history=history,
                                           action='move', move=line[len(history)]))
                self.assertEqual(state['status'], 'correct', p['number'])
                self.assertGreater(len(state['history']), len(history))
                history = state['history']
            self.assertEqual(history, line)


if __name__ == '__main__':
    unittest.main()
