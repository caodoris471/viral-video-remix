# 🔥 爆款视频自动抓取 → 混剪成新视频

<div align="center">

**抓同行爆款 · 拆爆款结构 · 写新文案 · AI 配音 · 自动配镜头 · 出剪映草稿**

一个给 Codex / Claude Code 用的 skill。发一句话安装，再说一句「帮我做一批混剪」就开工。

![平台](https://img.shields.io/badge/平台-Windows%2010%2F11-blue) ![配音](https://img.shields.io/badge/配音-16种语言-orange) ![适用](https://img.shields.io/badge/适用-Codex%20%7C%20Claude%20Code-purple) ![费用](https://img.shields.io/badge/费用-全部免费工具-green)

</div>

> **免责声明：** 本项目仅供学习研究。抓取只做只读、低频访问，请遵守各平台规则；爆款视频只借鉴结构，不搬运画面和文案，成片请使用你自己有权使用的实拍素材。

## 📖 项目简介

### 能帮谁

- **做种草/带货短视频的商家和运营**：手上有店铺、产品的实拍素材，不想每条都手动剪
- **做出海的团队**：同一套素材，要出英语、日语、西语等多个国家的版本
- **想测试「哪种爆款结构更有效」的人**：一批出 5 条，每条套一个不同爆款的结构，发布后对比数据

### 解决什么问题

| 以前 | 现在 |
|---|---|
| 刷半天找对标，手动记爆款结构 | 自动抓同行爆款和互动数据，逐句转写拆结构 |
| 文案写完才发现素材里没这个画面 | 先扫素材打标签，按素材写文案 |
| 录音口误、停顿多，要一句句剪 | 自动剪口误、压停顿、提速润色；或直接 AI 配音 |
| 一个镜头一个镜头找、对齐台词 | 按台词自动配镜头，避开原视频字幕自动裁 9:16 |
| 做完不知道哪种结构有效 | 每条带爆款结构编号 S1…Sn，自动出批次清单，填数据对比 |

### 🔧 原理

本地 Python 流水线：OpenCV 切镜头 → RapidOCR 识别烧录字幕并算出不碰字的裁切窗 → faster-whisper 给口播打逐字/逐词时间戳 → 按「每段画面必须有什么」打分配镜头 → ffmpeg 出预览、pyJianYingDraft 出剪映草稿。全部在本机跑，不用付费 API。

## ✨ 功能特性

| 环节 | 功能 | 状态 |
|---|---|---|
| 抓爆款 | 抖音 / 小红书 / 视频号 / B站 / 快手 / YouTube / TikTok / Instagram | ✅ |
| 拆结构 | 逐句转写、语速、每段时长、剪辑节奏（切点/秒） | ✅ |
| 素材 | 自动切镜头、避字幕裁 9:16、运动量、联系表打标签 | ✅ |
| 文案 | 和原爆款文字重合度检查（只借结构不抄） | ✅ |
| 配音 | AI 配音 16 种语言，只选男/女，自动用该语言最热门免费音色 | ✅ |
| 配音 | 真人录音：剪口误、压停顿、单句重录替换、不变调提速 | ✅ |
| 剪辑 | 按台词配镜头、同一镜头不重复、亮度统一、上下模糊填充 | ✅ |
| 包装 | 5 种花字大字随机样式 + 逐字弹出、Mixkit 音效和配乐自动下载 | ✅ |
| 交付 | 预览 MP4 + 剪映草稿（字幕、动画、关键帧都可改） | ✅ |
| 测试 | 爆款结构编号 S1…Sn + 批次清单 CSV（可导入飞书） | ✅ |

**支持的配音语言**：中文 · 英语(美/英) · 日语 · 韩语 · 西班牙语 · 葡萄牙语 · 法语 · 德语 · 意大利语 · 俄语 · 印尼语 · 马来语 · 越南语 · 菲律宾语 · 泰语

## 🚀 快速开始

> 💡 如果这个项目对你有帮助，请给个 ⭐ Star 支持一下！

### 方式一：一句话安装（推荐）

把这段话发给 Codex 或 Claude Code：

```
帮我安装这个 skill：https://github.com/caodoris471/viral-video-remix
把它 git clone 到你的 skills 目录（Codex 是 ~/.codex/skills，Claude Code 是 ~/.claude/skills），文件夹名 爆款视频混剪-viral-video-remix；然后运行里面的 一键安装.ps1，装完告诉我哪些通过、哪些要我手动处理。
采集对标用的 skill 也一起装：https://github.com/caodoris471/blogger-video-pipeline
```

装完开新对话说：

```
用 viral-video-remix 帮我做一批混剪
```

它会先问你 4 件事：**目标国家/语言**、**AI 配音还是真人配音**（AI 只问男声/女声）、**这批出几条**（= 几个爆款结构）、**品类和素材在哪**。答完自动往下跑。

### 方式二：手动安装

```powershell
git clone https://github.com/caodoris471/viral-video-remix "$HOME\.codex\skills\viral-video-remix"
cd "$HOME\.codex\skills\viral-video-remix"
powershell -ExecutionPolicy Bypass -File .\一键安装.ps1
```

Claude Code 用户把路径换成 `$HOME\.claude\skills\viral-video-remix`。国内连不上 GitHub 先开代理。分步骤图文说明见 [docs/安装底座.html](docs/安装底座.html)（下载后用浏览器打开）。

## 📋 用到的软件和 Skill

| 类别 | 名称 | 用途 | 安装 |
|---|---|---|---|
| Skill | [blogger-video-pipeline](https://github.com/caodoris471/blogger-video-pipeline) | 8 平台抓爆款、下载原片 | 一句话安装时一起装 |
| 运行环境 | Python 3.10+ | 跑全部脚本 | 一键安装（winget） |
| 运行环境 | ffmpeg | 剪辑、出预览、音频处理 | 一键安装（winget） |
| 运行环境 | git | 下载和更新 skill | 一键安装（winget） |
| 剪辑软件 | 剪映专业版 | 打开草稿微调、导出 | 手动安装，打开一次 |
| Python 包 | opencv-python / numpy | 切镜头、裁切、运动量 | 一键安装 |
| Python 包 | rapidocr_onnxruntime | 识别原视频字幕并避开 | 一键安装 |
| Python 包 | faster-whisper | 口播逐字时间戳、爆款转写（本地免费） | 一键安装 |
| Python 包 | edge-tts | AI 配音 16 种语言（免费） | 一键安装 |
| Python 包 | pyJianYingDraft | 生成剪映草稿 | 一键安装 |
| Python 包 | playwright | 抓取用浏览器 | 一键安装 |
| 素材 | Mixkit 免费音效/配乐 | 大字音效、转场、背景音乐 | 安装时自动从官网下载 |
| 字体（可选） | 汉仪雅酷黑 95W | 中文花字预览 | 手动安装 |

## ⚙️ 需要换成你自己的

新建项目：复制 `projects/_模板` 为 `projects/<你的项目名>`，改这几处（AI 会带你改）：

| 文件 | 字段 | 填什么 |
|---|---|---|
| config.json | `语言` | `zh` `en` `en-GB` `ja` `ko` `es` `pt` `fr` `de` `it` `ru` `id` `ms` `vi` `fil` `th` |
| config.json | `素材目录` | 你的原片文件夹，如 `D:/素材/北欧风` |
| config.json | `标签词表` | 按品类改，如服装：上身全身、面料特写、细节_领口 |
| 分镜_S1_AI.json | `爆款结构` / `对标链接` | S1…Sn，对应你文档里的「爆款结构1…n」 |
| 分镜_S1_AI.json | `草稿名` | 如 `北欧风_S1_AI_V1` |

## 🗺️ 完整流程

| # | 节点 | 工具 |
|---|---|---|
| 0 | 抓爆款 + 下载原片 | blogger-video-pipeline |
| 1 | 拆爆款结构 S1…Sn | `transcribe.py` `ref_compare.py` |
| 2 | 扫素材 + 打标签 | `scan.py` `summary.py` `tag_sheet.py` |
| 3 | 每个结构写一份文案（先对素材） | `overlap_check.py` |
| 4 | 口播（AI / 真人） | `tts_edge.py` `voice_prep.py` `voice_splice.py` `voice_speed.py` |
| 5 | 分镜 | `plan_beats.py` `coverage.py` |
| 6 | 配镜头 + 调色 | `match.py` `grade.py` |
| 7 | 出片（MP4 + 剪映草稿） | `render.py` |
| 8 | 自检 | `qa.py` `ref_compare.py` `shot_stats.py` |
| 9 | 批次清单 | `batch_list.py` |

每一步的输入输出、规则和踩过的坑见 [docs/流程SOP.html](docs/流程SOP.html)。

## ❓ 常见问题

- **出片报 `x264 malloc failed`**：电脑内存不够，关掉浏览器标签等占内存的程序再跑；4K 素材先缩到 1080p
- **剪映里看不到新草稿**：要先完全退出剪映（托盘也退），再双击 `安装到剪映.cmd`
- **AI 配音报 403**：`pip install -U edge-tts`
- **音效没声音**：运行 `python tools/get_sfx.py` 补下载

## ⭐ 支持项目

觉得有用就点个 Star；遇到问题或想要新功能，欢迎提 [Issue](https://github.com/caodoris471/viral-video-remix/issues)。

## 🙏 致谢

[pyJianYingDraft](https://github.com/GuanYixuan/pyJianYingDraft) · [faster-whisper](https://github.com/SYSTRAN/faster-whisper) · [RapidOCR](https://github.com/RapidAI/RapidOCR) · [edge-tts](https://github.com/rany2/edge-tts) · [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) · [Mixkit](https://mixkit.co)

## 📄 许可

Mixkit 音效配乐遵循 [Mixkit License](https://mixkit.co/license/)，由每台电脑自己从官网下载，本仓库不转发素材文件。
