"""Local, stateless book-line practice. Never equate an unlisted move with a loss."""
import json
from pathlib import Path
import chess

ROOT = Path(__file__).resolve().parent

def chapter(number):
    if type(number) is not int or number not in range(1, 5):
        raise ValueError('章节无效')
    return json.loads((ROOT / f'data/chapter{number:02}/chapter.json').read_text('utf-8'))

def catalog():
    result = []
    for n in range(1, 5):
        data = chapter(n)
        result.append({'number': n, 'title': data['chapter']['title'], 'puzzles': [
            {'number': p['number'], 'points': p['points'], 'pending': p.get('review_status', {}).get('answer') == 'pending_review'}
            for p in data['puzzles']]})
    return result

def play(data):
    puzzles = chapter(data.get('chapter'))['puzzles']
    p = next((p for p in puzzles if p['number'] == data.get('number')), None)
    if p is None:
        raise ValueError('题号不存在')
    history = data.get('history', [])
    if not isinstance(history, list) or len(history) > 200:
        raise ValueError('走法记录无效')
    board = chess.Board(p['fen']); sans = []; lines = [line['uci'] for line in p['book_lines']]
    for uci in history:
        move = chess.Move.from_uci(uci)
        if move not in board.legal_moves:
            raise ValueError('走法记录不合法，请重新开始')
        sans.append(board.san(move)); board.push(move)
    candidates = [line for line in lines if line[:len(history)] == history]
    if not candidates:
        raise ValueError('走法记录不在本题答案中，请重新开始')
    pending = p.get('review_status', {}).get('answer') == 'pending_review'
    action = data.get('action', 'state'); status = 'ready'
    if action == 'move':
        if pending:
            raise ValueError('本题答案待复核，暂不判题。')
        if board.turn != chess.Board(p['fen']).turn or any(len(line)==len(history) for line in candidates):
            raise ValueError('当前不能继续答题，请重新开始或选择下一题')
        try:
            move = chess.Move.from_uci(data.get('move', ''))
        except (ValueError, TypeError):
            raise ValueError('请选择起点和终点') from None
        if move not in board.legal_moves:
            status = 'illegal'
        else:
            matching = [line for line in candidates if len(line)>len(history) and line[len(history)]==move.uci()]
            if not matching:
                status = 'unlisted'
            else:
                sans.append(board.san(move)); board.push(move); history = [*history, move.uci()]
                candidates = matching
                status = 'correct'
                # Prefer a completed book branch, otherwise play its first recorded reply.
                if not any(len(line)==len(history) for line in candidates):
                    reply = chess.Move.from_uci(candidates[0][len(history)])
                    sans.append(board.san(reply)); board.push(reply); history.append(reply.uci())
                    candidates = [line for line in candidates if line[:len(history)]==history]
    elif action not in ('state', 'reveal'):
        raise ValueError('操作无效')
    complete = any(len(line)==len(history) for line in candidates)
    result = {'history':history, 'san':sans, 'fen':board.fen(),
        'pieces':{chess.square_name(s):pc.symbol() for s,pc in board.piece_map().items()},
        'legal_moves':[move.uci() for move in board.legal_moves], 'orientation':p['turn'],
        'status':status, 'complete':complete, 'checkmate':board.is_checkmate(), 'pending':pending,
        'number':p['number'], 'points':p['points'], 'turn':'white' if board.turn else 'black'}
    if action == 'reveal':
        result['answers'] = [line.get('transcribed_notation', ' '.join(line['san'])) for line in p['book_lines']]
        result['notes'] = p['notes']
    return result
