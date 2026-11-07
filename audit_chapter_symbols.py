"""Audit transcribed notation against actual positions, without treating ! as a rule."""
import json
from pathlib import Path
import chess

root=Path(__file__).parent/'data/chapter01'
data=json.loads((root/'chapter.json').read_text('utf-8'))
raw={int(l.split(' ',1)[0]):l.split(' ',1)[1] for l in (root/'answers.txt').read_text('utf-8-sig').splitlines()}
counts={'moves':0,'check_plus':0,'checkmate_hash':0,'double_check_symbol':0,'actual_double_checks':0}
issues=[]; details=[]
for p in data['puzzles']:
    for index,line in enumerate(raw[p['number']].split(' | ')):
        board=chess.Board(p['fen'])
        for token in line.split():
            move=board.parse_san(token); piece=board.piece_at(move.from_square)
            letter=token[0] if token[0] in 'KQRBN' else 'P'
            if piece.symbol().upper()!=letter: issues.append([p['number'],token,'棋子字母不匹配'])
            board.push(move); counts['moves']+=1
            attackers=len(board.checkers())
            if attackers>=2: counts['actual_double_checks']+=1
            if token.endswith('#'):
                counts['checkmate_hash']+=1
                if not board.is_checkmate():issues.append([p['number'],token,'并非将死'])
            elif token.endswith('++'):
                counts['double_check_symbol']+=1
                if attackers<2:issues.append([p['number'],token,'并非双将'])
            elif token.endswith('+'):
                counts['check_plus']+=1
                if not board.is_check():issues.append([p['number'],token,'并非将军'])
            elif board.is_check():issues.append([p['number'],token,'遗漏将军标记'])
        details.append({'number':p['number'],'branch':index+1,'line':line,'ends_in_mate':board.is_checkmate()})
    if not p['engine_check']['mate_in'] or p['engine_check']['mate_in']<=0:
        issues.append([p['number'],'engine','未确认起始行棋方强制将杀'])
report={'scope':'已转录的标准记谱答案及已保存的引擎检查；不是原书所有排版符号的逐字转录审计','counts':counts,'issues':issues,'lines':details,'limitations':['原书的!、?评价符号未在先前SAN转录中保存，不能声称已逐个验证。','++在本书表示双将；本次转录答案未使用++。实际双将也可以用标准SAN的+或#表达。','原书1-0与0-1未逐题单独序列化；引擎记录显示90题起始行棋方均可强制将杀，但不等于已逐个核对原书胜负标记。','引擎计算并非每题所有可能分支的穷尽证明。']}
(root/'符号验证报告.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'counts':counts,'issues':issues,'branches':len(details)},ensure_ascii=False))
