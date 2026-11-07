"""Build the portable chapter 2 package from reviewed photo transcriptions."""
import ast, io, json, pathlib, re, shutil, zipfile
import chess, chess.engine, chess.pgn, chess.svg

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / 'data/chapter02'
SOURCE = pathlib.Path('C:/Users/tiant/Desktop/第二章残局和答案')

def main():
    positions = {}
    for row in (OUT/'transcription.txt').read_text('utf-8-sig').splitlines():
        n, turn, *pieces = row.split()
        b = chess.Board(None)
        assert len({p[:2] for p in pieces}) == len(pieces)
        for p in pieces:
            b.set_piece_at(chess.parse_square(p[:2]), chess.Piece.from_symbol(p[2]))
        b.turn = turn == 'w'
        assert int(n) not in positions
        positions[int(n)] = b
    answers = {int(row.split(' ', 1)[0]): row.split(' ', 1)[1] for row in (OUT/'answers.txt').read_text('utf-8-sig').splitlines()}
    assert set(positions) == set(answers) == set(range(91, 145))
    records, games, errors = [], [], []
    counts = {'moves': 0, 'check': 0, 'mate': 0, 'double_check': 0, 'annotations': 0}
    notes = {94:'书中走到 Rb1+，说明下一步将杀。',98:'威胁 Be2# 或 Bd3#；书中指出直接 1...Bd3? 会被 2.Be5 挡住 e 线。',100:'原书 Rd8 未标将死；规范 SAN 根据实际局面补全。',105:'书中走到 Rb8+，说明下一步将杀。',110:'另给出 Rh8+ 的先后次序。',116:'威胁 Qg7#。',120:'书中走到 Rd8+，说明还需两步将杀。',128:'Ba3 分支未写完将杀过程。',129:'书中说明随后 Bh6#，未列出中间黑方走法。',130:'书中走到 Qa8+，说明随后将杀。',133:'书中两条分支均停在 Rc8+，说明下一步将杀。',137:'书中走到 Ra1+，说明再两步将杀。',139:'书中说明随后 Bh6#，未列出中间黑方走法。',141:'另提到 Re8 可赢得大量子力，未作为将杀主线录入。',142:'书中另外说明威胁 Qg2#；未虚构白方等待着。',144:'答案跨答案4.jpg、答案5.jpg。'}
    for n, board in sorted(positions.items()):
        if not board.is_valid(): errors.append(f'{n}: invalid board {board.status()}')
        game = chess.pgn.Game(); game.setup(board)
        game.headers['Event'] = f'Chapter 2 - Puzzle {n}'
        game.headers['Result'] = '1-0' if board.turn else '0-1'
        lines = []
        for raw in answers[n].split(' | '):
            b = board.copy(); node = game; sans = []; ucis = []
            try:
                for token in raw.split():
                    san = token.rstrip('!?'); annotation = token[len(san):]
                    move = b.parse_san(san); canonical = b.san(move)
                    b.push(move)
                    counts['moves'] += 1
                    if san.endswith('#'):
                        counts['mate'] += 1
                        if not b.is_checkmate(): errors.append(f'{n}: not mate: {token} ({canonical})')
                    elif san.endswith('++'):
                        counts['double_check'] += 1
                        if len(b.checkers()) < 2: errors.append(f'{n}: not double check: {token}')
                    elif san.endswith('+'):
                        counts['check'] += 1
                        if not b.is_check(): errors.append(f'{n}: not check: {token} ({canonical})')
                    sans.append(canonical); ucis.append(move.uci())
                    node = node.variation(move) if node.has_variation(move) else node.add_variation(move)
                    if annotation:
                        counts['annotations'] += 1
                        node.nags.add({'!':1, '?':2, '!!':3, '??':4, '!?':5, '?!':6}[annotation])
                lines.append({'san':sans, 'uci':ucis, 'transcribed_notation':raw, 'ends_in_checkmate':b.is_checkmate(), 'source':'book'})
            except ValueError as e: errors.append(f'{n}: {raw}: {e}')
        answer_pages = [1] if n<=103 else [2] if n<=116 else [3] if n<=130 else [4] if n<=143 else [4,5]
        if n in (104,117,131): answer_pages.insert(0, answer_pages[0]-1)
        records.append({'id':f'ch02-{n:03}', 'number':n, 'points':1 if n<=106 else 2 if n<=125 else 3 if n<=140 else 4 if n<=143 else 5, 'fen':board.fen(), 'turn':'white' if board.turn else 'black', 'goal':{'type':'checkmate'}, 'book_lines':lines, 'source_image':f'images/{(n-91)//6+1}.jpg', 'answer_image':f'images/答案{answer_pages[-1]}.jpg', 'answer_images':[f'images/答案{p}.jpg' for p in answer_pages], 'diagram_index':(n-91)%6, 'validation':{'legal_position':board.is_valid(), 'book_moves_legal':len(lines)==len(answers[n].split(' | '))}, 'notes':[notes[n]] if n in notes else []})
        games.append(str(game))
    (OUT/'validation-errors.txt').write_text('\n'.join(errors), encoding='utf-8')
    if errors:
        print('\n'.join(errors)); return
    engine = chess.engine.SimpleEngine.popen_uci(str(ROOT/'engines/stockfish-19/stockfish/stockfish-windows-x86-64-universal.exe'))
    try:
        engine.configure({'Threads':2, 'Hash':128})
        for p in records:
            b = chess.Board(p['fen']); first = chess.Move.from_uci(p['book_lines'][0]['uci'][0])
            info = engine.analyse(b, chess.engine.Limit(time=.5), root_moves=[first])
            score = info['score'].pov(b.turn); san = []; uci = []
            for move in info.get('pv', []):
                san.append(b.san(move)); uci.append(move.uci()); b.push(move)
            p['engine_check'] = {'engine':'Stockfish 19', 'search_seconds':.5, 'depth':info.get('depth'), 'mate_in':score.mate(), 'score_cp':score.score(), 'san':san, 'uci':uci, 'source':'engine_supplement_not_book'}
    finally: engine.quit()
    data = {'format':'interchess-book', 'schema_version':1, 'book_title':'少儿国际象棋·初级篇（页脚：1001个绝妙将杀）', 'chapter':{'number':2, 'title':'底线将杀'}, 'assumptions':{'castling':'none','en_passant':'none','halfmove_clock':0,'fullmove_number':1}, 'puzzles':records}
    (OUT/'chapter.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    (OUT/'chapter.pgn').write_text('\n\n'.join(games), encoding='utf-8')
    (OUT/'images').mkdir(exist_ok=True)
    for path in SOURCE.glob('*.jpg'): shutil.copy2(path, OUT/'images'/path.name)
    viewer = []
    for p in records:
        frames = []
        for line in p['book_lines']:
            b = chess.Board(p['fen']); orientation = b.turn
            arr = [chess.svg.board(b,size=420,orientation=orientation)]
            for uci in line['uci']:
                m = chess.Move.from_uci(uci); b.push(m)
                arr.append(chess.svg.board(b,size=420,orientation=orientation,lastmove=m))
            frames.append(arr)
        viewer.append({**p, 'frames':frames})
    tree = ast.parse((ROOT/'package_chapter.py').read_text('utf-8'))
    template = next(node.value.func.value.value for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(t,ast.Name) and t.id=='page' for t in node.targets))
    template = template.replace('第一章','第二章').replace('简单将杀','底线将杀').replace('90 道题','54 道题')
    template = template.replace('<a id="solution" target="_blank">查看答案原图</a>', '<span id="solution"></span>')
    template = template.replace("$('solution').href=p.answer_image;", "$('solution').replaceChildren();p.answer_images.forEach((path,i)=>{let a=document.createElement('a');a.href=path;a.target='_blank';a.textContent='答案原图 '+(i+1)+' ';$('solution').append(a)});")
    template = template.replace("data[index].book_lines[variant].san.join(' ')", "data[index].book_lines[variant].transcribed_notation")
    page = template.replace('PAYLOAD',json.dumps(viewer,ensure_ascii=False).replace('</','<\\/'))
    (OUT/'打开第二章.html').write_text(page,encoding='utf-8')
    report = {'puzzles':len(records), 'book_lines':sum(len(p['book_lines']) for p in records), 'symbol_checks':counts, 'engine_mate_found':sum(p['engine_check']['mate_in'] is not None for p in records), 'errors':errors, 'limitations':['引擎搜索是辅助验证，不是逐格识别正确性的证明。','!/? 为原书评价，保留但不作为规则正确性判据。','未标 +/# 的走法在 SAN 中自动补全；原始转录保留在 transcribed_notation。','书中结果表示胜负，并不表示当前局面已将死。']}
    (OUT/'validation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'README.txt').write_text('第二章：底线将杀，91—144题，共54题，116分。\n解压整个文件夹，双击“打开第二章.html”即可离线浏览，Windows和Mac通用，无需API或安装引擎。\nchapter.json 保存FEN、主线与分支、标准SAN/UCI及原书评价符号；chapter.pgn 可供棋谱软件导入。\nbook_lines 为照片转录；engine_check 为引擎补充，不是原书答案。原书中文讲解未全文转录，请查 images 中答案照片。跨页答案见 answer_images。\n所有局面、答案走法及已标注的将军/将死符号均经过规则检查。!表示好棋，?表示坏棋，属原书评价，不能仅靠规则检验。\n网页用于浏览、隐藏答案和逐步演示，不支持自由走棋判题。王车易位权、吃过路兵默认无。\n',encoding='utf-8')
    stream = io.StringIO((OUT/'chapter.pgn').read_text('utf-8')); count = 0
    while (g:=chess.pgn.read_game(stream)) is not None:
        assert not g.errors and g.board().fen()==records[count]['fen']; count += 1
    assert count == 54 and sum(p['points'] for p in records)==116
    for p in records:
        assert all((OUT/x).exists() for x in [p['source_image'],*p['answer_images']])
    archive = ROOT/'第二章-底线将杀-54题.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for path in OUT.rglob('*'):
            if path.is_file(): z.write(path,'第二章-底线将杀/'+path.relative_to(OUT).as_posix())
    with zipfile.ZipFile(archive) as z: assert z.testzip() is None
    print(json.dumps(report,ensure_ascii=False)); print(archive,archive.stat().st_size)

if __name__ == '__main__': main()
