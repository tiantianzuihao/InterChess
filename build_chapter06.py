"""Build chapter 6 from manually reviewed photos; reject illegal lines/symbols."""
import ast
import io
import json
from pathlib import Path
import zipfile

import chess
import chess.engine
import chess.pgn
import chess.svg
from PIL import Image

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'data/chapter06'
NOTES = {
    303: '原书只列 Rg1!，说明威胁 Nf4#，未给白方等待着；不补造走法。',
    325: 'Kf8 分支原书停在 Bf6+，并未走到将死。',
    330: '原书另推荐 Ne4+，该分支未列后续。',
    335: '原书停在 fxg6，说明白方仍胜；未列完整将杀。',
    338: 'Ra2+ 分支原书在 Kh3 后说明下一步威胁 Rf7#，未给黑方等待着。',
    342: '原书反例 Qg7+? Kxg7 Re8 Rxe8 是错误走法，不作为正确答案。',
    345: '第二次 Kf8 分支原书停在 Bh6+，未列后续将杀。',
    346: '原书反例 h3? Rg1 不作为正确答案；f3 后威胁 Rg2#，收录书中 Rg1 Rh3# 分支。',
    349: '主线停在 Bf6，说明威胁 Rh8#；Qc7 分支停在 Qf8+，未补造应手。原书 Bd4? e5 为反例。',
}


def main():
    positions = {}
    for row in (OUT / 'transcription-reviewed.txt').read_text('utf-8-sig').splitlines():
        if not row.strip():
            continue
        number, turn, *pieces = row.split()
        board = chess.Board(None)
        assert len({p[:2] for p in pieces}) == len(pieces)
        for p in pieces:
            board.set_piece_at(chess.parse_square(p[:2]), chess.Piece.from_symbol(p[2]))
        board.turn = turn == 'w'
        assert board.is_valid(), (number, board.status())
        assert int(number) not in positions
        positions[int(number)] = board
    answers = {}
    for row in (OUT / 'answers-reviewed.txt').read_text('utf-8-sig').splitlines():
        if row.strip():
            n, answer = row.split(' ', 1)
            assert int(n) not in answers
            answers[int(n)] = answer
    assert set(positions) == set(answers) == set(range(301, 355))
    records, games = [], []
    counts = dict(moves=0, check=0, mate=0, double_check=0)
    for n, board in sorted(positions.items()):
        game = chess.pgn.Game()
        game.setup(board)
        game.headers['Event'] = f'Chapter 6 - Puzzle {n}'
        game.headers['Result'] = '1-0' if board.turn else '0-1'
        lines = []
        for raw in answers[n].split(' | '):
            b, node, sans, ucis = board.copy(), game, [], []
            for token in raw.split():
                san = token.rstrip('!?')
                move = b.parse_san(san[:-1] if san.endswith('++') else san)
                canonical = b.san(move)
                b.push(move)
                counts['moves'] += 1
                if san.endswith('#'):
                    assert b.is_checkmate(), (n, token)
                    counts['mate'] += 1
                elif san.endswith('++'):
                    assert len(b.checkers()) >= 2, (n, token)
                    counts['double_check'] += 1
                elif san.endswith('+'):
                    assert b.is_check(), (n, token)
                    counts['check'] += 1
                sans.append(canonical)
                ucis.append(move.uci())
                node = node.variation(move) if node.has_variation(move) else node.add_variation(move)
                annotation = token[len(san):]
                if annotation:
                    node.nags.add({'!': 1, '?': 2, '!!': 3, '??': 4, '!?': 5, '?!': 6}[annotation])
            lines.append(dict(san=sans, uci=ucis, transcribed_notation=raw,
                              ends_in_checkmate=b.is_checkmate(), source='book'))
        page = 1 if n < 307 else (n - 307) // 6 + 7
        answer_pages = [1 if n <= 316 else 2 if n <= 330 else 3 if n <= 343 else 4 if n <= 353 else 5]
        if n in (331, 344):
            answer_pages.insert(0, answer_pages[0] - 1)
        records.append(dict(id=f'ch06-{n}', number=n,
                            points=1 if n <= 308 else 2 if n <= 326 else 3 if n <= 345 else 4 if n <= 352 else 5,
                            fen=board.fen(), turn='white' if board.turn else 'black', goal={'type': 'checkmate'},
                            book_lines=lines, source_image=f'images/{page}.jpg',
                            answer_image=f'images/答案{answer_pages[-1]}.jpg',
                            answer_images=[f'images/答案{p}.jpg' for p in answer_pages],
                            diagram_index=(n - 301) % 6,
                            validation={'legal_position': True, 'book_moves_legal': True, 'symbols_valid': True, 'photo_reviewed': True},
                            notes=[NOTES[n]] if n in NOTES else []))
        games.append(str(game))

    import duel
    with chess.engine.SimpleEngine.popen_uci(duel.engine_path()) as engine:
        engine.configure({'Threads': 2, 'Hash': 128})
        for p in records:
            b = chess.Board(p['fen'])
            first = chess.Move.from_uci(p['book_lines'][0]['uci'][0])
            info = engine.analyse(b, chess.engine.Limit(time=0.75), root_moves=[first])
            score = info['score'].pov(b.turn)
            seconds = 0.75
            if score.mate() is None:
                seconds = 8
                info = engine.analyse(b, chess.engine.Limit(time=seconds), root_moves=[first])
                score = info['score'].pov(b.turn)
            p['engine_check'] = dict(engine='Stockfish 19', search_seconds=seconds, depth=info.get('depth'),
                                     mate_in=score.mate(), score_cp=score.score(),
                                     source='engine_supplement_not_book')
            print(p['number'], 'mate', score.mate(), 'cp', score.score(), flush=True)

    report = dict(puzzles=len(records), book_lines=sum(len(p['book_lines']) for p in records),
                  symbol_checks=counts, errors=[],
                  incomplete_book_lines=[p['number'] for p in records if any(not l['ends_in_checkmate'] for l in p['book_lines'])],
                  engine_mate_found=sum(p['engine_check']['mate_in'] is not None for p in records),
                  engine_needs_review=[p['number'] for p in records if p['engine_check']['mate_in'] is None],
                  limitations=['引擎短时搜索为辅助检查，不证明照片逐格识别完全正确。',
                               '原书省略的吃子 x 已规范化；原书评价 !/? 保留，不以走棋规则判定其好坏。',
                               '未补造原书省略的应手；获胜结果不等同于局面已经将死。'])
    data = dict(format='interchess-book', schema_version=1, book_title='少儿国际象棋·初级篇（1001个绝妙将杀）',
                chapter={'number': 6, 'title': '车和轻子配合的将杀'},
                assumptions={'castling': 'none', 'en_passant': 'none', 'halfmove_clock': 0, 'fullmove_number': 1},
                import_status={'reviewed': list(positions), 'remaining': []}, puzzles=records)
    (OUT / 'chapter.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), 'utf-8')
    (OUT / 'chapter.pgn').write_text('\n\n'.join(games), 'utf-8')
    (OUT / 'validation-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
    stream = io.StringIO((OUT / 'chapter.pgn').read_text('utf-8'))
    for p in records:
        game = chess.pgn.read_game(stream)
        assert game and not game.errors and game.board().fen() == p['fen']
        assert all((OUT / x).is_file() for x in [p['source_image'], *p['answer_images']])
    assert chess.pgn.read_game(stream) is None

    viewer = []
    for p in records:
        frames = []
        for line in p['book_lines']:
            b = chess.Board(p['fen'])
            orientation = b.turn
            arr = [chess.svg.board(b, size=420, orientation=orientation)]
            for uci in line['uci']:
                m = chess.Move.from_uci(uci)
                b.push(m)
                arr.append(chess.svg.board(b, size=420, orientation=orientation, lastmove=m))
            frames.append(arr)
        viewer.append({**p, 'frames': frames})
    tree = ast.parse((ROOT / 'package_chapter.py').read_text('utf-8'))
    template = next(node.value.func.value.value for node in tree.body if isinstance(node, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == 'page' for t in node.targets))
    template = template.replace('第一章', '第六章').replace('简单将杀', '车和轻子配合的将杀').replace('90 道题', '54 道题')
    (OUT / '打开第六章.html').write_text(template.replace('PAYLOAD', json.dumps(viewer, ensure_ascii=False).replace('</', '<\\/')), 'utf-8')
    make_review(records)
    status = dict(chapter=6, first=301, last=354, count=54, status='photo_reviewed_rules_validated_imported', photos=19)
    (OUT / 'IMPORT-STATUS.json').write_text(json.dumps(status, ensure_ascii=False, indent=2), 'utf-8')
    manifest_path = ROOT / 'data/remaining-import-status.json'
    manifest = json.loads(manifest_path.read_text('utf-8'))
    manifest['chapters'][0] = status
    manifest['next_step'] = 'Chapter 6 imported. Chapters 7-9 remain unverified drafts; review one chapter at a time.'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), 'utf-8')
    (OUT / 'README.txt').write_text('第六章：车和轻子配合的将杀，301—354题，共54题。\n双击“打开第六章.html”可离线浏览。chapter.json 与 chapter.pgn 为便携数据。\n原书未写完整的变化不补造应手，详见 validation-report.json 和各题 notes。\n', 'utf-8')
    with zipfile.ZipFile(ROOT / '第六章-车和轻子配合的将杀-54题.zip', 'w', zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
        for path in OUT.rglob('*'):
            if path.is_file() and 'review' not in path.relative_to(OUT).parts and path.name != 'recognition-draft.json':
                archive.write(path, '第六章-车和轻子配合的将杀/' + path.relative_to(OUT).as_posix())
    print(json.dumps(report, ensure_ascii=False))


def make_review(records):
    dest = ROOT / 'web/review-chapter06'
    dest.mkdir(exist_ok=True)
    drafts = json.loads((OUT / 'recognition-draft.json').read_text('utf-8'))
    if isinstance(drafts, dict):
        drafts = drafts['puzzles']
    index = {p['number']: p for p in drafts}
    items = []
    for p in records:
        n = p['number']
        board = chess.Board(p['fen'])
        (dest / f'{n}.svg').write_text(chess.svg.board(board, size=600), 'utf-8')
        draft = index[n]
        if not (dest / f'{n}.jpg').exists():
            im = Image.open(OUT / 'review' / Path(p['source_image']).name)
            xs, ys = zip(*draft['box'])
            x, y = min(xs), min(ys)
            w, h = max(xs) - x, max(ys) - y
            crop = im.crop((max(0, int(x * im.width) - 25), max(0, int(y * im.height) - 90),
                            min(im.width, int((x + w) * im.width) + 25), min(im.height, int((y + h) * im.height) + 35)))
            crop.thumbnail((650, 750))
            crop.save(dest / f'{n}.jpg', quality=92)
        items.append(dict(number=n, turn='白方先走' if board.turn else '黑方先走', notes=p['notes'],
                          lines=[l['transcribed_notation'] for l in p['book_lines']]))
    template = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>第六章题面对照</title>
<style>body{font:18px system-ui;background:#f7f5ef;color:#233c33;margin:24px auto;max-width:1200px;padding:0 18px}button,select{font:inherit;padding:10px;margin:5px;border:1px solid #acb9ab;border-radius:8px;background:white}.pair{display:grid;grid-template-columns:1fr 1fr;gap:24px}img{width:100%;max-height:680px;object-fit:contain}#notes{background:#fff0d5;padding:16px;white-space:pre-wrap}pre{white-space:pre-wrap} @media(max-width:700px){.pair{grid-template-columns:1fr}}</style>
<h1>第六章 · 原图与已核对题面对照</h1><p>301～354 题已逐格核对并通过走法、将军和将死符号检查。若与原书不符，请告诉我题号、格子和棋子。两侧均为白方在下。</p>
<a href="/practice.html">返回残局练习</a><div><button id="prev">上一题</button><select id="select"></select><button id="next">下一题</button><span id="turn"></span></div>
<div id="notes"></div><div class="pair"><section><h2>书本原图</h2><img id="photo" alt="书本棋盘照片"></section><section><h2>已导入题面</h2><img id="board" alt="已导入棋盘"></section></div><details><summary>核对答案文字（家长）</summary><pre id="lines"></pre></details>
<script>const data=PAYLOAD;const s=document.getElementById('select');for(const p of data){const o=document.createElement('option');o.value=p.number;o.textContent='第 '+p.number+' 题';s.append(o)}function show(){const p=data.find(p=>p.number===+s.value);document.getElementById('photo').src=p.number+'.jpg';document.getElementById('board').src=p.number+'.svg';document.getElementById('turn').textContent=p.turn;const notes=document.getElementById('notes');notes.textContent=p.notes.join('\\n');notes.hidden=!p.notes.length;document.getElementById('lines').textContent=p.lines.join('\\n');history.replaceState(null,'','#'+p.number)}s.onchange=show;for(const [id,d] of [['prev',-1],['next',1]])document.getElementById(id).onclick=()=>{s.selectedIndex=(s.selectedIndex+d+data.length)%data.length;show()};if(data.some(p=>p.number===+location.hash.slice(1)))s.value=+location.hash.slice(1);show()</script></html>'''
    (dest / 'index.html').write_text(template.replace('PAYLOAD', json.dumps(items, ensure_ascii=False).replace('</', '<\\/')), 'utf-8')


if __name__ == '__main__':
    main()
