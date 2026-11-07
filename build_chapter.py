import json, pathlib, shutil, zipfile, io
import chess, chess.pgn, chess.engine, chess.svg
ROOT=pathlib.Path(__file__).parent
OUT=ROOT/'data/chapter01'
SOURCE=pathlib.Path('C:/Users/tiant/Desktop/第一章残局和答案')
def build():
    positions={}
    for line in (OUT/'transcription.txt').read_text('utf-8-sig').splitlines():
        n,turn,*pieces=line.split(); b=chess.Board(None)
        for p in pieces: b.set_piece_at(chess.parse_square(p[:2]),chess.Piece.from_symbol(p[2]))
        b.turn=turn=='w'; positions[int(n)]=b
    for p in json.loads((ROOT/'web/demo.json').read_text('utf-8'))['puzzles']:
        b=chess.Board(None)
        for sq,pc in p['pieces'].items(): b.set_piece_at(chess.parse_square(sq),chess.Piece.from_symbol(pc))
        b.turn=p['number']!='78'; positions[int(p['number'])]=b
    answers={int(l.split(' ',1)[0]):l.split(' ',1)[1] for l in (OUT/'answers.txt').read_text('utf-8-sig').splitlines()}
    records=[]; errors=[]; games=[]
    for n,b in sorted(positions.items()):
        if not b.is_valid(): errors.append(f'{n}: invalid board {b.status()}')
        lines=[]; game=chess.pgn.Game(); game.setup(b); game.headers['Event']=f'Chapter 1 - Puzzle {n}'
        for raw in answers[n].split(' | '):
            pos=b.copy(); ucis=[]; sans=[]; node=game
            try:
                for san in raw.split():
                    move=pos.parse_san(san); canonical=pos.san(move)
                    if san.endswith('#') and not canonical.endswith('#'): errors.append(f'{n}: not mate {san} ({canonical})')
                    sans.append(canonical); ucis.append(move.uci()); pos.push(move)
                    node=node.variation(move) if node.has_variation(move) else node.add_variation(move)
                lines.append({'san':sans,'uci':ucis,'ends_in_checkmate':pos.is_checkmate(),'source':'book'})
            except ValueError as e: errors.append(f'{n}: {e}')
        page=(n-1)//6+1
        answer='大.jpg' if n<=18 else f'答案{1 if n<=34 else 2 if n<=48 else 3 if n<=64 else 4 if n<=80 else 5}.jpg'
        records.append({'id':f'ch01-{n:03}','number':n,'points':1 if n<=14 else 2,'fen':b.fen(),'turn':'white' if b.turn else 'black','goal':{'type':'checkmate'},'book_lines':lines,'source_image':f'images/{page}.jpg','answer_image':f'images/{answer}','diagram_index':(n-1)%6,'validation':{'legal_position':b.is_valid(),'book_moves_legal':len(lines)==len(answers[n].split(' | '))},'notes': []})
        games.append(str(game))
    (OUT/'validation-errors.txt').write_text('\n'.join(errors),encoding='utf-8')
    (OUT/'chapter.json').write_text(json.dumps({'format':'interchess-book','schema_version':1,'book_title':'少儿国际象棋·初级篇（页脚：1001个绝妙将杀）','chapter':{'number':1,'title':'简单将杀'},'assumptions':{'castling':'none','en_passant':'none','halfmove_clock':0,'fullmove_number':1},'puzzles':records},ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'chapter.pgn').write_text('\n\n'.join(games),encoding='utf-8')
    print('\n'.join(errors) or f'{len(records)} positions and all book lines validated')
    return records
if __name__=='__main__': build()
