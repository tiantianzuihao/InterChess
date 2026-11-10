"""Cross-platform double-click launcher. Only listens on localhost."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import socket
import subprocess
import sys
import tarfile
import threading
import time
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parent
URL = 'http://127.0.0.1:18765'
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def health():
    try:
        with OPENER.open(URL + '/api/health', timeout=1) as response:
            data = json.load(response)
        return data.get('app') == 'InterChess'
    except (OSError, ValueError):
        return False

def port_busy():
    try:
        with socket.create_connection(('127.0.0.1',18765), timeout=.5): return True
    except OSError: return False

def open_home():
    print('打开首页 / Open: ' + URL, flush=True)
    try: webbrowser.open(URL)
    except Exception: pass

def acquire_lock(path):
    handle = path.open('a+b')
    try:
        if os.fstat(handle.fileno()).st_size == 0: handle.write(b'0'); handle.flush()
        handle.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return None
    return handle

def prepare_environment():
    env = ROOT / ('.venv' if os.name == 'nt' else '.venv-macos' if sys.platform == 'darwin' else '.venv-linux')
    python = env / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.exists():
        print('首次启动：创建本地 Python 环境… / Creating environment', flush=True)
        subprocess.run([sys.executable,'-m','venv',str(env)], check=True)
    requirements = ROOT/'requirements.txt'
    fingerprint = hashlib.sha256(requirements.read_bytes()).hexdigest()
    stamp = env/'.interchess-requirements'
    probe = subprocess.run([str(python),'-c','import cv2, PIL, chess, numpy'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if probe.returncode or not stamp.exists() or stamp.read_text() != fingerprint:
        print('检查并安装依赖；首次安装需要联网。 / Installing dependencies', flush=True)
        subprocess.run([str(python),'-m','pip','install','-r',str(requirements)],check=True)
        stamp.write_text(fingerprint)
    return python

def prepare_mac_engine():
    if sys.platform != 'darwin' or os.getenv('STOCKFISH_PATH'): return
    engines = ROOT/'engines'
    found = next(engines.rglob('stockfish-macos-universal'),None) if engines.exists() else None
    archive = engines/'downloads/stockfish-macos-universal.tar.gz'
    if found is None and archive.exists():
        destination = engines/'stockfish-macos'
        destination.mkdir(exist_ok=True)
        with tarfile.open(archive) as source:
            members = source.getmembers()
            for member in members:
                target = (destination/member.name).resolve()
                if not target.is_relative_to(destination.resolve()) or not (member.isfile() or member.isdir()):
                    raise ValueError('引擎压缩包含不安全路径或特殊文件，停止解压。')
            # All members have been checked; no links or special files are allowed.
            for member in members:
                target = destination/member.name
                if member.isdir(): target.mkdir(parents=True,exist_ok=True)
                else:
                    target.parent.mkdir(parents=True,exist_ok=True)
                    with source.extractfile(member) as inp, target.open('wb') as out:
                        import shutil
                        shutil.copyfileobj(inp,out)
        found = next(destination.rglob('stockfish-macos-universal'),None)
    if found:
        found.chmod(found.stat().st_mode | 0o111)
    else:
        print('提示：未携带 Mac 引擎，残局练习可用；人机对弈请配置引擎。',flush=True)

def serve():
    prepare_mac_engine()
    def browse_when_ready():
        for _ in range(100):
            if health(): open_home(); return
            time.sleep(.2)
        print('服务未就绪，请查看此窗口的错误信息。',flush=True)
    threading.Thread(target=browse_when_ready,daemon=True).start()
    print('InterChess 已启动。保留此窗口；按 Ctrl+C 停止服务。',flush=True)
    runpy.run_path(str(ROOT/'server.py'),run_name='__main__')

def main():
    os.chdir(ROOT)
    if '--serve' in sys.argv: serve(); return 0
    if sys.version_info < (3,10): raise RuntimeError('需要 Python 3.10 或更新版本。')
    if not (ROOT/'server.py').exists(): raise RuntimeError('请将启动器放在 InterChess 项目根目录。')
    if health():
        print('服务已在运行，直接打开首页。',flush=True);open_home();return 0
    runtime = ROOT/'.runtime';runtime.mkdir(exist_ok=True)
    lock = acquire_lock(runtime/'launcher.lock')
    if lock is None:
        print('另一个启动器正在准备，请稍候…',flush=True)
        for _ in range(150):
            if health():open_home();return 0
            time.sleep(.2)
        raise RuntimeError('已有启动窗口正在准备，请查看那个窗口。')
    with lock:
        if health(): open_home();return 0
        if port_busy(): raise RuntimeError('端口 18765 被其他程序或旧版服务占用，请先关闭该程序后重试。')
        python = prepare_environment()
        child = subprocess.Popen([str(python),str(ROOT/'launcher.py'),'--serve'],cwd=ROOT)
        try: return child.wait()
        except KeyboardInterrupt:
            if child.poll() is None:
                # Console Ctrl+C also reaches the child; allow engine cleanup first.
                try: child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.terminate()
                    try: child.wait(timeout=5)
                    except subprocess.TimeoutExpired: child.kill();child.wait()
            return 0

if __name__ == '__main__':
    try: sys.exit(main())
    except KeyboardInterrupt: sys.exit(0)
    except Exception as error:
        print('启动失败 / Could not start: ' + str(error), file=sys.stderr, flush=True)
        sys.exit(1)
