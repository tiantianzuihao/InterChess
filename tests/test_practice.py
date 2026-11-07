import unittest
import practice


class PracticeTests(unittest.TestCase):
    def test_every_main_line_and_pending_review(self):
        for ch in practice.catalog():
            for p in practice.chapter(ch['number'])['puzzles']:
                request = {'chapter':ch['number'], 'number':p['number']}
                state = practice.play(request)
                if p['number'] == 231:
                    self.assertTrue(state['pending'])
                    with self.assertRaises(ValueError):
                        practice.play({**request, 'action':'move', 'move':p['book_lines'][0]['uci'][0]})
                    continue
                line = p['book_lines'][0]['uci']
                while not state['complete']:
                    state = practice.play({**request, 'action':'move', 'history':state['history'], 'move':line[len(state['history'])]})
                    self.assertEqual(state['status'], 'correct', p['id'])
                self.assertEqual(state['history'], line[:len(state['history'])])

    def test_unlisted_move_does_not_change_position_or_mark_wrong(self):
        request = {'chapter':4, 'number':235}
        original = practice.play(request)
        book_moves = {line['uci'][0] for line in practice.chapter(4)['puzzles'][0]['book_lines']}
        alternative = next(m for m in original['legal_moves'] if m not in book_moves)
        result = practice.play({**request,'action':'move','move':alternative})
        self.assertEqual(result['status'], 'unlisted')
        self.assertEqual(result['fen'], original['fen'])
        self.assertEqual(result['history'], [])

    def test_answers_hidden_until_requested(self):
        request = {'chapter':4,'number':235}
        self.assertNotIn('answers', practice.play(request))
        self.assertTrue(practice.play({**request,'action':'reveal'})['answers'])
        with self.assertRaises(ValueError):
            practice.play({**request,'history':['a1a8']})

if __name__ == '__main__':
    unittest.main()
