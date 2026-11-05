import json
from pathlib import Path
import cv2
from server import detect_boards

root = Path(__file__).parent
im = cv2.imread(str(root / 'web/sample.jpg'))
boards, found = detect_boards(im)
print('Detected six boards:', found)
positions = [
 'b7:b b6:P c6:p f6:p h6:p f5:B f4:K h4:k f3:P g2:P',
 'e8:R f8:b g8:k f7:p h7:p d6:P f6:Q f5:p h4:P a3:p b3:P g3:P a2:r d2:q g2:B h1:K',
 'e8:n b7:p c7:R d7:b f7:r h6:p b5:P d5:k f5:P g5:p b4:B d4:P f4:b d3:B f3:K h3:P',
 'a7:p f7:R b6:p f6:Q g6:r h6:k c5:p d4:P e4:P g4:p c3:P d3:q h3:r a2:P b2:P h2:P e1:R g1:K',
 'c8:k a7:r b7:R g7:p c6:n f6:p g6:n c5:N d5:p f5:N h5:p d4:P h4:P g3:P f2:P g2:K',
 'b8:R a7:p f7:p b6:p e6:P g6:p f4:k h4:K c3:r h3:P',
]
data = {'puzzles': [{'number': str(73+i), 'points': boards[i], 'pieces': dict(s.split(':') for s in text.split()),
    'uncertain': [], 'turn': '', 'castle': '-', 'ep': '-', 'confirmed': False,
    'source': '预录示例', 'note': '按照片预先转录。三角标记含义尚未确认，请核对行棋方。'} for i, text in enumerate(positions)]}
(root / 'web/demo.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
