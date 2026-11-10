#!/bin/bash
cd -- "$(dirname -- "$0")" || exit 1
export PYTHONUTF8=1
for candidate in "$PWD/.venv-macos/bin/python" /opt/homebrew/bin/python3 /usr/local/bin/python3 python3; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' >/dev/null 2>&1; then
        "$candidate" launcher.py
        result=$?
        if [ "$result" -ne 0 ]; then
            printf '\n启动失败。按回车关闭窗口 / Press Return to close.\n'
            read -r
        fi
        exit "$result"
    fi
done
printf '未找到 Python 3.10+。请从 https://www.python.org/downloads/macos/ 安装后重试。\n'
printf 'Python 3.10+ is required. Press Return to close.\n'
read -r
exit 1
