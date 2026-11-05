import json
import unittest
from pathlib import Path
import chess
import cv2
import numpy as np
from server import detect_boards, crop, validate_fen, recognize

ROOT = Path(__file__).resolve().parents[1]

class CoreTests(unittest.TestCase):
    def test_sample_positions(self):
        data = json.loads((ROOT / 'web/demo.json').read_text('utf-8'))
        self.assertEqual(len(data['puzzles']), 6)
        for p in data['puzzles']:
            board = chess.Board(None)
            for square, piece in p['pieces'].items():
                board.set_piece_at(chess.parse_square(square), chess.Piece.from_symbol(piece))
            board.turn = p['number'] != '78'
            self.assertTrue(board.is_valid(), (p['number'], board.status()))
            self.assertEqual(chess.Board(board.fen()).piece_map(), board.piece_map())

    def test_photo_detection_and_crop(self):
        im = cv2.imread(str(ROOT / 'web/sample.jpg'))
        boxes, found = detect_boards(im)
        self.assertTrue(found)
        self.assertEqual(len(boxes), 6)
        for points in boxes:
            warped = crop(im, points)
            self.assertEqual(warped.shape, (800, 800, 3))
            self.assertGreater(warped.std(), 10)

    def test_empty_photo_fallback(self):
        boxes, found = detect_boards(np.ones((900, 600, 3), dtype=np.uint8)*255)
        self.assertFalse(found)
        self.assertEqual(len(boxes), 6)

    def test_illegal_position_rejected(self):
        self.assertFalse(validate_fen('8/8/8/8/8/8/8/8 w - - 0 1')['valid'])
        self.assertFalse(validate_fen('8/8/8/8/8/8/4k3/4K3 w - - 0 1')['valid'])

    def test_invalid_crop_rejected(self):
        with self.assertRaises(ValueError):
            crop(np.zeros((500,500,3), dtype=np.uint8), [[0,0]]*4)

if __name__ == '__main__':
    unittest.main()
