import unittest
import chess
import practice

class ChapterFiveTests(unittest.TestCase):
    def test_catalog_and_all_book_lines(self):
        data=practice.chapter(5)
        self.assertEqual(data['chapter']['title'],'兵升变将杀')
        self.assertEqual([p['number'] for p in data['puzzles']],list(range(271,301)))
        self.assertIn(5,[c['number'] for c in practice.catalog()])
        self.assertEqual(sum(p['points'] for p in data['puzzles']),93)
        for p in data['puzzles']:
            for line in p['book_lines']:
                board=chess.Board(p['fen'])
                self.assertTrue(board.is_valid(),p['number'])
                for uci,san in zip(line['uci'],line['san']):
                    move=chess.Move.from_uci(uci)
                    self.assertIn(move,board.legal_moves,p['number'])
                    self.assertEqual(board.san(move),san)
                    board.push(move)
                self.assertEqual(board.is_checkmate(),line['ends_in_checkmate'])
    def test_underpromotions_in_practice(self):
        for number,promotion in [(278,'r'),(289,'n'),(300,'n')]:
            p=next(p for p in practice.chapter(5)['puzzles'] if p['number']==number)
            history=[]
            for uci in p['book_lines'][0]['uci']:
                if len(uci)==5 and uci.endswith(promotion):
                    state=practice.play({'chapter':5,'number':number,'history':history,'action':'move','move':uci})
                    self.assertEqual(state['status'],'correct')
                    self.assertIn(uci,state['history'])
                    break
                history.append(uci)
            else:self.fail(f'Underpromotion not found: {number}')
