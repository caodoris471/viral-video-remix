---
name: real-footage-montage
description: 实拍素材+口播自动混剪成 9:16 种草/带货短视频（多语言 AI 口播或真人口播，一批多条、每条对应一个爆款结构），产出预览 MP4、剪映草稿和批次清单。用户说"做混剪/实拍混剪/换个品类做一批/口播配素材/测试爆款结构"时使用。
---

# 实拍混剪自动化

本 skill 所在目录记为 `$KIT`（含 tools/、projects/、音效库/、docs/）。所有命令在 `$KIT` 下运行。第一次用先跑 `一键安装.cmd`（或 `powershell -ExecutionPolicy Bypass -File 一键安装.ps1`）。

## 开工前必问（一次问完，用提问工具给选项）

1. **目标国家/语言**：中国(zh) / 美国(en) / 英国(en-GB) / 日本(ja) / 韩国(ko) / 墨西哥·西语(es) / 巴西(pt) / 法国(fr) / 德国(de) / 意大利(it) / 俄罗斯(ru) / 印尼(id) / 马来(ms) / 越南(vi) / 菲律宾(fil) / 泰国(th)。
2. **配音方式**：AI 配音 / 真人配音（用户自己录） / 两版都要。
   - 选 AI：只问**男声还是女声**，不问具体音色。自动用该语言最热门的免费音色（`--gender=男|女`；中文男=云希，女=晓晓）。
   - 选真人：让用户按文稿录音，放进 `inputs/`。
3. **批次规模**：这批出几条成片（如 5 条），对应几个爆款结构（每条一个结构 S1…Sn）。对标视频一共几条、链接或文件在哪。
4. **品类和素材**：品类名、原片在哪（没有就先走采集）。

## 编号规则（用于后续测试爆款结构，必须遵守）

- 爆款结构编号 `S1…Sn`，与飞书/文档里的「爆款结构1…n」一一对应。每个结构记下对标视频链接。
- 文案、分镜、成片都带同一个编号：`inputs/文稿_S1.txt` → `分镜_S1_AI.json`（字段 `爆款结构: "S1"`、`对标链接`）→ 草稿名 `品类_S1_AI_V1`。
- 一批出完跑 `python tools/batch_list.py projects/<项目>` 生成 `批次清单.csv`（结构、对标链接、文案、成片路径，后面留空列填发布数据），交给用户导入飞书做对比。
- 同一条成片里同一原镜头只用一次；不同成片之间可以复用素材。

## 硬规则

- 回复用户用中文（成片语言按第 1 问）。
- 镜头 1.5–4 秒；只在句间/逗号停顿切；画面必须含该段「必需」标签；缺镜头就停下报缺，不凑；静态镜头 ≤5；转场 ≤3。
- 先对素材再写文案，素材够了再录口播/生成配音。
- 文案口语化（中文不要文言腔）；外语文案按当地口语写；和参考稿 `overlap_check.py` 必须通过，只借结构不抄文字。
- key 只读环境变量，不打印、不写文件。

## 流程

0. **新项目**：复制 `projects/_模板` → `projects/<项目>`；改 config.json：`语言`、`名称`、`素材目录`、`标签词表`（按品类改）。
1. **采集对标和原片**：用 skill **blogger-video-pipeline**（https://github.com/caodoris471/blogger-video-pipeline ，支持抖音/小红书/视频号/B站/快手/YouTube/TikTok/Instagram）。没装就先装：`git clone https://github.com/caodoris471/blogger-video-pipeline <skills目录>/blogger-video-pipeline`。下载的原片放进 config 的素材目录。
2. **拆解爆款结构**：`python tools/transcribe.py work/拆解 <对标视频…> --lang=<代码>` → 每条写成结构 S1…Sn（钩子 / 要点数 / 每段秒数 / 语速 / 结尾引导）；`python tools/ref_compare.py work/拆解 <对标视频…>` 量剪辑节奏。
3. **扫素材+打标签**：`python tools/scan.py projects/<项目>` → `python tools/summary.py projects/<项目>` → 看 `work/sheets/*.png` 写 `work/tags.json`（只标裁切后清楚可见的；口播人像/效果图/画中画/后期标注要标出来）。
4. **写文案**：每个结构一份 `inputs/文稿_Sn.txt`，一句一行。每句列「画面必须有什么」，对照 tags 每类 ≥2 个 ≥4 秒窗；不够先补素材或改句。
5. **口播**（每份文稿）：
   - AI：`python tools/tts_edge.py inputs/文稿_S1.txt inputs/S1_AI.mp3 --lang=<代码> --gender=<男|女>` → `python tools/voice_prep.py inputs/S1_AI.mp3 inputs/文稿_S1.txt work/口播_S1_AI --lang=<代码>`
   - 真人：`python tools/voice_prep.py <录音> inputs/文稿_S1.txt work/口播_S1 --lang=<代码>` → 有重录 `python tools/voice_splice.py work/口播_S1 work/口播_S1b 2=<重录>` → `python tools/voice_speed.py work/口播_S1b work/口播_S1_快 1.25`
6. **分镜**：`python tools/plan_beats.py projects/<项目> <timestamps.json>` → 写 `分镜_S1_AI.json`（爆款结构/对标链接/句/起字/要点/必需/优先/关键词/出转场；英语等语言「起字」是第几个词，关键词写口播原词）→ `python tools/coverage.py projects/<项目> 分镜_S1_AI.json`，合格数 0 的段先补。
7. **配镜头+调色**：`python tools/match.py projects/<项目> 分镜_S1_AI.json` → `python tools/grade.py projects/<项目> EDL_S1_AI.json`
8. **出片**：`python tools/render.py projects/<项目> EDL_S1_AI.json`
9. **自检**：`python tools/qa.py projects/<项目> S1_AI` 全过，逐格看 `检查_逐段对照.png`；`ref_compare.py` 对比节奏（目标 ≈0.35 切/秒，中位 ≈2.5 秒）。
10. 对每个结构重复 4–9；全部完成后 `python tools/batch_list.py projects/<项目>`。
11. **交付**：给出每条预览 MP4 路径和批次清单；提醒「先完全退出剪映，再双击 output/<版本>/安装到剪映.cmd」。

## 常见问题

- 重扫后窗号变了：`python tools/remap_tags.py projects/<项目>/work`
- 4K 素材或内存不足（x264 malloc failed）：先 ffmpeg 缩到 1080p，关掉占内存的程序再出片
- 音效库为空：`python tools/get_sfx.py` 从 Mixkit 官网下载（出片时缺文件也会自动补下）
- edge-tts 403：`pip install -U edge-tts`
- 项目搬家：`python tools/repath.py <目录> <旧前缀> <新前缀>`
- 详细说明：`docs/流程SOP.html`、`docs/安装底座.html`
