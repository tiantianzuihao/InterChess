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

## 人机博弈

首页的「人机博弈」已接入本地 Stockfish，无需 API 密钥或在线服务。
8 档依次使用 Skill Level 0、2、5、8、11、14、17、20，单步思考上限分别为 0.10、0.15、0.25、0.40、0.60、0.80、1.00、1.50 秒。临近超时会缩短思考时间。这些是本应用等级，不是 Lichess 等级或固定 Elo；实际强度受硬件影响，1 级也可能对初学者有挑战。
支持白方、黑方、随机；无限时，或每方 1～180 分钟加每步 0～60 秒。服务端计时，落子成功后加秒。超时会判负，对方子力不足时判和；三次重复或 50 回合可申请和棋，五次重复和 75 回合自动判和。
刷新可继续当前标签页的对局；对局保存在服务内存，重启服务会清空，关闭页面不会暂停棋钟。
引擎自动查找 engines 下对应平台的可执行文件，也支持环境变量 STOCKFISH_PATH。Mac 需先解压官方包并给予执行权限；Windows 上已实测，Mac 仍需在目标机验证。
人机对弈暂未启用 Syzygy，以保持各档难度设置一致。
