"""Local Stockfish games with server-owned boards and monotonic clocks."""
import atexit
import os
import secrets
import shutil
import sys
import threading
import time
from pathlib import Path
import chess
import chess.engine
from practice import describe_moves

ROOT = Path(__file__).resolve().parent
# UI level: (Stockfish skill, maximum think time in seconds).
LEVELS = [(0,.10),(2,.15),(5,.25),(8,.4),(11,.6),(14,.8),(17,1.0),(20,1.5)]
GAMES = {}
GAMES_LOCK = threading.Lock()
ENGINE_LOCK = threading.Lock()
ENGINE = None

def engine_path():
    configured = os.getenv('STOCKFISH_PATH')
    if configured:
        if Path(configured).is_file(): return configured
        raise ValueError('STOCKFISH_PATH 指向的引擎不存在。')
    name = 'stockfish-windows-x86-64-universal.exe' if sys.platform == 'win32' else 'stockfish-macos-universal' if sys.platform == 'darwin' else 'stockfish'
    found = next((ROOT / 'engines').rglob(name), None)
    if found: return str(found)
    found = shutil.which('stockfish')
    if found: return found
    raise ValueError('未找到本地 Stockfish，请安装引擎或设置 STOCKFISH_PATH。')

def get_engine():
    global ENGINE
    if ENGINE is None:
        kwargs = {'creationflags': 0x08000000} if sys.platform == 'win32' else {}
        try:
            ENGINE = chess.engine.SimpleEngine.popen_uci(engine_path(), timeout=10, **kwargs)
            ENGINE.configure({'Threads':1, 'Hash':64})
        except (OSError, chess.engine.EngineError) as exc:
            ENGINE = None
            raise ValueError('本地 Stockfish 启动失败，请检查可执行权限和引擎路径。') from exc
    return ENGINE

@atexit.register
def close_engine():
    if ENGINE:
        try: ENGINE.quit()
        except Exception: pass

class Game:
    def __init__(self, level, color, minutes, increment):
        self.board = chess.Board()
        self.level = level
        self.human = secrets.choice([True, False]) if color == 'random' else color == 'white'
        self.remaining = {True:minutes*60.0, False:minutes*60.0} if minutes else None
        self.increment = increment
        self.stamp = time.monotonic()
        self.result = None
        self.lock = threading.Lock()
        self.touched = self.stamp

    def tick(self):
        now = time.monotonic()
        if self.remaining is not None and self.result is None:
            color = self.board.turn
            self.remaining[color] = max(0, self.remaining[color] - (now-self.stamp))
            if self.remaining[color] <= 0:
                winner = not color
                draw = self.board.has_insufficient_material(winner)
                self.result = {'winner':None if draw else ('white' if winner else 'black'), 'reason':'超时，另一方子力不足，和棋' if draw else '超时'}
        self.stamp = now
        self.touched = now

    def push(self, move):
        mover = self.board.turn
        self.board.push(move)
        if self.remaining is not None: self.remaining[mover] += self.increment
        self.stamp = time.monotonic()
        outcome = self.board.outcome(claim_draw=False)
        if outcome:
            reasons = {chess.Termination.CHECKMATE:'将死',chess.Termination.STALEMATE:'逼和',chess.Termination.INSUFFICIENT_MATERIAL:'子力不足',chess.Termination.SEVENTYFIVE_MOVES:'75 回合规则',chess.Termination.FIVEFOLD_REPETITION:'五次重复局面'}
            self.result = {'winner':None if outcome.winner is None else ('white' if outcome.winner else 'black'), 'reason':reasons.get(outcome.termination,'和棋')}

    def snapshot(self):
        return {'pieces':{chess.square_name(s):p.symbol() for s,p in self.board.piece_map().items()},
                'fen':self.board.fen(), 'legal_moves':[m.uci() for m in self.board.legal_moves] if not self.result else [],
                'history':[m.uci() for m in self.board.move_stack],
                'move_details':describe_moves(chess.STARTING_FEN,[m.uci() for m in self.board.move_stack]),
                'turn':'white' if self.board.turn else 'black', 'human':'white' if self.human else 'black',
                'level':self.level, 'increment':self.increment, 'result':self.result,
                'checked_king':chess.square_name(self.board.king(self.board.turn)) if self.board.is_check() else None,
                'clocks':None if self.remaining is None else {'white':self.remaining[True],'black':self.remaining[False]},
                'can_claim_draw':not self.result and self.board.can_claim_draw()}

def handle(data):
    global ENGINE
    action = data.get('action')
    if action == 'new':
        level, color = data.get('level'), data.get('color')
        minutes, increment = data.get('minutes',0), data.get('increment',0)
        if type(level) is not int or level not in range(1,9) or color not in ('white','black','random'):
            raise ValueError('请选择 1～8 级和执棋方。')
        if type(minutes) is not int or not 0 <= minutes <= 180 or type(increment) is not int or not 0 <= increment <= 60:
            raise ValueError('时间应为 0～180 分钟，加秒为 0～60 秒。')
        with ENGINE_LOCK: get_engine()
        game = Game(level,color,minutes,increment if minutes else 0)
        token = secrets.token_urlsafe(24)
        with GAMES_LOCK:
            for key in list(GAMES):
                if time.monotonic()-GAMES[key].touched > 86400: del GAMES[key]
            if len(GAMES) >= 128: raise ValueError('对局数量过多，请重启本地服务。')
            GAMES[token] = game
        return {'id':token, **game.snapshot()}
    token = data.get('id')
    if not isinstance(token,str): raise ValueError('对局不存在，请重新开局。')
    with GAMES_LOCK: game = GAMES.get(token)
    if game is None: raise ValueError('对局已失效，请重新开局。')
    with game.lock:
        game.tick()
        if action == 'move' and not game.result:
            if game.board.turn != game.human: raise ValueError('请等待电脑落子。')
            try: move = chess.Move.from_uci(data.get('move',''))
            except (ValueError,TypeError): raise ValueError('走法无效。') from None
            if move not in game.board.legal_moves: raise ValueError('这步不符合走棋规则。')
            game.push(move)
        elif action == 'engine' and not game.result and game.board.turn != game.human:
            with ENGINE_LOCK:
                game.tick()
                if not game.result:
                    skill, seconds = LEVELS[game.level-1]
                    if game.remaining: seconds = min(seconds,max(.01,game.remaining[game.board.turn]/20))
                    try:
                        engine = get_engine()
                        engine.configure({'Skill Level':skill,'UCI_LimitStrength':False})
                        choice = engine.play(game.board, chess.engine.Limit(time=seconds), game=token)
                    except (chess.engine.EngineError, TimeoutError) as exc:
                        close_engine(); ENGINE = None
                        raise ValueError('引擎暂时不可用，请点击重试。') from exc
                    game.tick()
                    if not game.result and choice.move: game.push(choice.move)
        elif action == 'resign' and not game.result:
            game.result = {'winner':'black' if game.human else 'white','reason':'认输'}
        elif action == 'claim' and not game.result:
            if game.board.turn != game.human or not game.board.can_claim_draw(): raise ValueError('当前不能申请和棋。')
            game.result = {'winner':None,'reason':'三次重复或 50 回合规则'}
        elif action not in ('state','move','engine','resign','claim'):
            raise ValueError('操作无效。')
        return {'id':token, **game.snapshot()}
