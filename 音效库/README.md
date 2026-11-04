# 音效库

安装时自动从 Mixkit 官网下载（`python tools/get_sfx.py`），出片时发现缺文件也会自动补下。仓库本身不带文件，因为 Mixkit 许可不允许再分发素材文件；每台电脑自己从官网下载是允许的，成片可免费商用。许可：https://mixkit.co/license/

| 文件 | 用途 |
|---|---|
| mixkit_2354 / 2357 | pop：大字弹出 |
| mixkit_1491 / 1492 / 1486 | whoosh：转场 |
| mixkit_190 | wood：敲击强调 |
| mixkit_937 / 938 | chime：结尾提问 |
| mixkit_1430 / 1431 | shutter：快门 |
| music_801 / 5 / 621 / 1072 | 配乐 |

想换别的：从 mixkit.co 下载放进来，在项目 config.json 的 `音效` / `配乐` 改文件名。
