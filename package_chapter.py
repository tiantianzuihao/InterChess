import json, pathlib, shutil, zipfile, html
import chess, chess.engine, chess.svg, chess.pgn, io
from build_chapter import build, OUT, SOURCE, ROOT
records=build()
assert not (OUT/'validation-errors.txt').read_text('utf-8').strip()
notes={22:'书中另提到 1...Rb8 可以延缓一步。',23:'书中说明黑方威胁下一步 h6#。',24:'黑王移开后，白方威胁 Rh3#。',31:'威胁 Qh7#；书中给出 ...Qf6 的防守分支。',39:'威胁 Be2# 或 Rg6#。',40:'黑方无法阻止 Ra8#。',46:'威胁 Qb7#。',48:'威胁 Rf6#；...Rd6+ 可以延缓将杀。',49:'威胁 Ra4#。',73:'黑方无法阻挡下一步 g3#。'}
engine=chess.engine.SimpleEngine.popen_uci(str(ROOT/'engines/stockfish-19/stockfish/stockfish-windows-x86-64-universal.exe'))
engine.configure({'Threads':2,'Hash':128})
for p in records:
    b=chess.Board(p['fen']); first=chess.Move.from_uci(p['book_lines'][0]['uci'][0])
    result=engine.analyse(b,chess.engine.Limit(time=.15),root_moves=[first])
    score=result['score'].pov(b.turn); seq=[]; uci=[]
    for move in result.get('pv',[]): seq.append(b.san(move)); uci.append(move.uci()); b.push(move)
    p['engine_check']={'engine':'Stockfish 19','search_seconds':.15,'depth':result.get('depth'),'mate_in':score.mate(),'score_cp':score.score(),'san':seq,'uci':uci,'source':'engine_supplement_not_book'}
    if p['number'] in notes:p['notes'].append(notes[p['number']])
engine.quit()
data=json.loads((OUT/'chapter.json').read_text('utf-8')); data['puzzles']=records
(OUT/'chapter.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'images').mkdir(exist_ok=True)
for path in SOURCE.glob('*.jpg'):shutil.copy2(path,OUT/'images'/path.name)
viewer=[]
for p in records:
    frames=[]
    for line in p['book_lines']:
        b=chess.Board(p['fen']); arr=[chess.svg.board(b,size=420,orientation=b.turn)]
        orientation=b.turn
        for m in line['uci']:
            move=chess.Move.from_uci(m); b.push(move); arr.append(chess.svg.board(b,size=420,orientation=orientation,lastmove=move))
        frames.append(arr)
    viewer.append({**p,'frames':frames})
payload=json.dumps(viewer,ensure_ascii=False).replace('</','<\\/')
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>第一章 · 简单将杀</title><style>body{font:16px system-ui;background:#f4f3ed;color:#243a30;max-width:1000px;margin:30px auto;padding:16px}button,select{padding:10px;margin:4px;border:1px solid #b9cbbd;border-radius:8px;background:white}main{display:flex;gap:30px;flex-wrap:wrap}#board{width:min(90vw,440px)}aside{flex:1;min-width:260px}#answer{background:white;padding:16px;border-radius:12px}p{line-height:1.8}small{color:#67776b}a{color:#285e45}</style><h1>第一章 · 简单将杀</h1><p>90 道题 · 离线浏览 · 原书答案与引擎补充分开保存</p><button onclick="pick(-1)">上一题</button><select id="select" onchange="show(+this.value)"></select><button onclick="pick(1)">下一题</button><main><div id="board"></div><aside><h2 id="title"></h2><p id="turn"></p><button onclick="reveal()">显示书中答案</button><div id="answer" hidden><select id="line" onchange="branch()"></select><p id="moves"></p><button onclick="step(-1)">上一步</button><button onclick="step(1)">下一步</button><p id="notes"></p><small id="engine"></small></div><p><a id="source" target="_blank">查看题目原图</a> · <a id="solution" target="_blank">查看答案原图</a></p><small>此页面用于浏览和逐步演示，尚不支持自由走棋判题。原书只给出首步的题目，后续请看原图或数据中的引擎补充。</small><p><a href="chapter.json" download>JSON 数据</a> · <a href="chapter.pgn" download>PGN 数据</a></p></aside></main><script>const data=PAYLOAD;let index=0,variant=0,ply=0;const $=id=>document.getElementById(id);data.forEach((p,i)=>{let o=document.createElement('option');o.value=i;o.textContent='第 '+p.number+' 题';$('select').append(o)});function show(i){index=(i+data.length)%data.length;variant=0;ply=0;const p=data[index];$('select').value=index;$('title').textContent='第 '+p.number+' 题 · '+p.points+' 分';$('turn').textContent=(p.turn==='white'?'白方':'黑方')+'走：寻找将杀';$('answer').hidden=true;$('line').replaceChildren();p.book_lines.forEach((l,j)=>{let o=document.createElement('option');o.value=j;o.textContent='书中变化 '+(j+1);$('line').append(o)});$('notes').textContent=p.notes.join(' ');$('engine').textContent='引擎辅助检查：'+(p.engine_check.mate_in?'找到 '+p.engine_check.mate_in+' 步将杀':'有限搜索结果，详见 JSON');$('source').href=p.source_image;$('solution').href=p.answer_image;draw()}function draw(){$('board').innerHTML=data[index].frames[variant][ply];$('moves').textContent=data[index].book_lines[variant].san.join(' ')+'（演示 '+ply+' / '+(data[index].frames[variant].length-1)+'）'}function reveal(){$('answer').hidden=false}function pick(d){show(index+d)}function branch(){variant=+$('line').value;ply=0;draw()}function step(d){ply=Math.max(0,Math.min(ply+d,data[index].frames[variant].length-1));draw()}show(0);</script></html>'''.replace('PAYLOAD',payload)
(OUT/'打开第一章.html').write_text(page,encoding='utf-8')
(OUT/'README.txt').write_text('第一章：简单将杀，题号1—90。\n解压整个文件夹，双击“打开第一章.html”即可离线浏览，无需安装Python、Stockfish或配置API。Windows与Mac通用。\nchapter.json 为版本1的结构化数据；chapter.pgn 可导入支持FEN起始局面的棋谱软件。\nbook_lines 是照片转录的书中主线与分支；engine_check 是Stockfish辅助计算，不能当作书中原文。\n原图保存在images目录。文字讲解未全文转录，请查看答案原图；主要将杀威胁补充于notes。\n王车易位权和吃过路兵默认为无，半回合计数0，回合1。61、88题原图均为实心黑三角，表示黑方走，与答案一致。\n90题均通过局面合法性、答案走法合法性检查。对标有#的答案检查了实际将杀；合法性检查和引擎验证不能替代逐格人工复核。\n网页版仅支持浏览与演示，非互动判题器。学习进度不写入题库。\n',encoding='utf-8')
# Round-trip every PGN and JSON position before packaging.
stream=io.StringIO((OUT/'chapter.pgn').read_text('utf-8')); count=0
while (g:=chess.pgn.read_game(stream)) is not None:
    assert not g.errors; assert g.board().fen()==records[count]['fen']; count+=1
assert count==90
archive=ROOT/'第一章-简单将杀-90题.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
    for path in OUT.rglob('*'):
        if path.is_file() and not path.name.startswith('check') and path.name != 'viewer-check.js':z.write(path,'第一章-简单将杀/'+path.relative_to(OUT).as_posix())
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print('Packaged:',archive,'bytes:',archive.stat().st_size)
print('Engine mate confirmed:',sum(p['engine_check']['mate_in'] is not None for p in records),'/ 90')
