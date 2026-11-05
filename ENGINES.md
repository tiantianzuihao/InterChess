# 本地引擎与残局库

这些下载内容位于忽略 Git 跟踪的 `engines/` 目录。复制到另一台电脑时需要单独携带；只克隆 GitHub 仓库不会包含它们。

## Stockfish 19

- Windows 可执行文件：`engines/stockfish-19/stockfish/stockfish-windows-x86-64-universal.exe`
- macOS 官方通用版压缩包：`engines/downloads/stockfish-macos-universal.tar.gz`
- 官方来源：https://github.com/official-stockfish/Stockfish/releases/tag/sf_19
- Mac 包 SHA256：`a1f0e3bcc5a6927a11fe6fc8e54a779754645f3c2bae2cf13420fd1957adaa77`

Mac 上解压压缩包，使用其中的 `stockfish/stockfish-macos-universal`。该文件无法在 Windows 上执行，因此 Mac 运行测试需在目标机器进行。保留压缩包中的许可证与说明。

## Syzygy 3～5 子库

- 目录：`engines/syzygy/3-4-5/`
- 290 个数据文件，包含胜和负数据 `.rtbw` 和距离归零数据 `.rtbz`。
- 棋子总数包含双方王。Windows、macOS、Linux 使用相同的数据文件。
- 来源：https://tablebase.lichess.ovh/tables/standard/
- 每个文件对照来源提供的 SHA256 校验，清单保存在该目录的 `SHA256SUMS.txt`。
- 完整复制目录到 Mac 后，将引擎的 `SyzygyPath` 设置为 Mac 上该目录的绝对路径。

引擎原生命令示例（路径需按实际位置修改）：

```text
uci
setoption name SyzygyPath value D:\InterChess\engines\syzygy\3-4-5
isready
```

Python 连接示例：

```python
import chess.engine
engine = chess.engine.SimpleEngine.popen_uci("引擎可执行文件的路径")
engine.configure({"SyzygyPath": "残局库目录的绝对路径"})
# 使用 engine.analyse 或 engine.play
engine.quit()
```

`download_tablebases.py` 可补齐下载并重新校验已有文件。需要代理时设置 `TABLEBASE_PROXY` 环境变量。脚本只下载 3～5 子库，不下载六子或七子库。

注意：下载和测试引擎、残局库不等于已把它们接入网页。当前网页的本地引擎分析和陪练功能仍需实现。
