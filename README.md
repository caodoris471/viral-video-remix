# 🔥 爆款视频自动抓取 → 混剪成新视频

<div align="center">

**抓同行爆款 · 拆爆款结构 · 写新文案 · AI 配音 · 自动配镜头 · 出剪映草稿**

一个给 Codex / Claude Code 用的 skill。可以发账号主页和产品图启动带货混剪，也可以给关键词寻找对标；已有参数直接沿用。

![平台](https://img.shields.io/badge/平台-Windows%2010%2F11-blue) ![配音](https://img.shields.io/badge/配音-16种语言-orange) ![适用](https://img.shields.io/badge/适用-Codex%20%7C%20Claude%20Code-purple) ![费用](https://img.shields.io/badge/费用-全部免费工具-green)

</div>

> **免责声明：** 本项目仅供学习研究。抓取只做只读、低频访问，请遵守各平台规则；爆款视频只借鉴结构，不搬运画面和文案，成片请使用你自己有权使用的实拍素材。

## 📖 项目简介

### 能帮谁

- **做种草/带货短视频的商家和运营**：手上有店铺、产品的实拍素材，不想每条都手动剪
- **做出海的团队**：同一套素材，要出英语、日语、西语等多个国家的版本
- **想测试「哪种结构更有效」的人**：一批制作不同切入、脚本与镜头顺序，记录主参考和改编变体，发布后对比数据

### 解决什么问题

| 以前 | 现在 |
|---|---|
| 刷半天找对标，手动记爆款结构 | 自动抓同行爆款和互动数据，逐句转写拆结构 |
| 文案写完才发现素材里没这个画面 | 先扫素材打标签，按素材写文案 |
| 录音口误、停顿多，要一句句剪 | 自动剪口误、压停顿、提速润色；或直接 AI 配音 |
| 一个镜头一个镜头找、对齐台词 | 按台词自动配镜头，逐镜检查原字幕处理与主体构图 |
| 做完不知道哪种结构有效 | 每条带爆款结构编号 S1…Sn，固定素材编号关联主对标与画面来源，填数据对比 |

### 🔧 原理

本地 Python 流水线：OpenCV 切镜头 → RapidOCR 识别烧录字幕并算出不碰字的裁切窗 → faster-whisper 给口播打逐字/逐词时间戳 → 按「每段画面必须有什么」打分配镜头 → ffmpeg 出预览、pyJianYingDraft 出剪映草稿。剪辑和草稿生成在本机执行。平台采集和在线 AI 配音需要网络。

RapidOCR只识字，不会修复字幕背后的画面；本包没有内置视频字幕擦除插件。制作时先检查可用的擦除工具，清理后保留原构图并检查残字、闪烁和主体变形；工具不可用时说明缺口，优先无字素材或轻裁切。上下模糊填充是可选排版，不能默认用大幅裁切替代字幕清理。外接擦除工具的费用与可用性另行核实。

## ✨ 功能特性

| 环节 | 功能 | 状态 |
|---|---|---|
| 抓爆款 | 指定账号主页 / 关键词搜索 / 指定视频与本地素材三种入口；记录实际范围与指标证据 | ✅ |
| 拆结构 | 逐句转写、语速、每段时长、剪辑节奏（切点/秒） | ✅ |
| 开工 | 账号主页 + 清晰产品图即可启动；数量、每条大概时长、语言、门槛、功效等只补问缺项 | ✅ |
| 素材 | 自动切镜头和生成联系表。产品类按商品和用法复核通过后入剪 | ✅ |
| 文案 | 每条独立脚本与镜头顺序，标清主参考及改编变体；检查原稿重合度 | ✅ |
| 配音 | AI 配音 16 种语言，只选男/女，自动用该语言最热门免费音色 | ✅ |
| 配音 | 真人录音：剪口误、压停顿、单句重录替换、不变调提速 | ✅ |
| 剪辑 | 按台词配镜头、亮度统一；全动态模式拒绝静态主画面与整屏图片，角标可保留 | ✅ |
| 字幕 | 按实际字体测宽，外语长句按词时间戳分屏，预览与剪映使用同一字幕内容 | ✅ |
| 包装 | 5 种花字、Mixkit 配乐。透明 PNG 可全程叠加并在剪映独立编辑 | ✅ |
| 交付 | 记录实测时长，按需验收硬性时长范围，输出 MP4 与可编辑剪映草稿 | ✅ |
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

它会确认 **目标国家/语言、配音方式、批次数量与来源、每条大概时长、商品/主题与素材**；已给出的答案直接沿用，只补问缺项。约一分钟按内容和节奏自然收尾，明确给范围时再卡点，不默认只做20–40秒。

也可以直接这样发：

```text
从这个 TikTok 账号主页筛选播放量大于1000的冰箱清洁视频。
这是我的产品图和三项主推功效，产品放右下角。
用马来语女声先做1条预览，约1分钟，主画面不要定格。
```

发**账号主页 + 产品图**时，可以先建产品档案和采集参考，不要求额外提供关键词。清晰白底图可先接收，再处理成透明角标；缺少功效或用法依据时补问。关键词模式则跨账号发现候选，两种采集入口都可用于产品类或非产品类。详情见[采集入口与批量续作](docs/采集入口与批量续作.md)。

产品类按商品形态、用法和功效筛选画面，按需要用 PNG 做角标、自家实拍配演示。用户明确不提供自家演示并授权使用采集场景时，只使用通过准入的通用动作，不声称是自家实测。装修、旅游等非产品类按主题与场景选片。详见[产品带货素材准入](docs/产品带货素材准入.md)。

### 方式二：手动安装

```powershell
git clone https://github.com/caodoris471/viral-video-remix "$HOME\.codex\skills\爆款视频混剪-viral-video-remix"
cd "$HOME\.codex\skills\爆款视频混剪-viral-video-remix"
powershell -ExecutionPolicy Bypass -File .\一键安装.ps1
```

Claude Code 用户把路径换成 `$HOME\.claude\skills\爆款视频混剪-viral-video-remix`。国内连不上 GitHub 先开代理。分步骤图文说明见 [docs/安装底座.html](docs/安装底座.html)（下载后用浏览器打开）。

## 📋 用到的软件和 Skill

| 类别 | 名称 | 用途 | 安装 |
|---|---|---|---|
| Skill | [blogger-video-pipeline](https://github.com/caodoris471/blogger-video-pipeline) | 8 平台抓爆款、下载原片 | 一句话安装时一起装 |
| 运行环境 | Python 3.10+ | 跑全部脚本 | 一键安装（winget） |
| 运行环境 | ffmpeg | 剪辑、出预览、音频处理 | 一键安装（winget） |
| 运行环境 | git | 下载和更新 skill | 一键安装（winget） |
| 剪辑软件 | 剪映专业版 | 打开草稿微调、导出 | 手动安装，打开一次 |
| Python 包 | opencv-python / numpy | 切镜头、裁切、运动量 | 一键安装 |
| Python 包 | Pillow | 校验透明 PNG 和生成 TikTok 抽帧联系表 | 一键安装 |
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
| config.json | `目标时长秒` / `时长容差秒` | 填写每条的参考时长，默认容差留空。约一分钟按内容和节奏剪，偏离较多时自检只提醒。用户明确给范围时填容差，严格卡点填 0。批内不同时长可在单条分镜覆盖 |
| config.json | `任务类型` / `素材目录` | 产品类使用准入裁片目录，非产品类使用主题素材目录，如 `D:/素材/北欧风` |
| config.json | `采集` | 记录账号主页、关键词或指定素材，以及筛选指标、运算符和门槛；播放量与点赞分开 |
| config.json / 单条分镜 | `画面模式` | `自动`沿用静态名额；`全动态`将静态名额设为0，不使用整屏图，产品角标仍独立显示 |
| config.json | `规则.字幕安全宽度比例` | 字幕实际宽度占画布宽的上限，默认0.86；定制渲染字体/字号时同步测量 |
| config.json / 单条分镜 | `产品角标` | 选填透明 PNG 绝对路径及宽度、右距、底距，尺寸为画布像素 |
| config.json | `标签词表` | 按品类改，如服装：上身全身、面料特写、细节_领口 |
| 分镜_S1_AI.json | `爆款结构` / `对标链接` | S1…Sn，对应你文档里的「爆款结构1…n」 |
| 分镜_S1_AI.json | `草稿名` | 如 `北欧风_S1_AI_V1` |

飞书入库使用「固定素材编号 + 平台原视频ID（文本）+ S1…Sn」对齐，不依赖表格行号。素材库多选标签区分主结构对标与画面用途，成片表关联原片并填写原片/成片时间段；详见 [飞书编号与引用对齐](docs/飞书编号与引用对齐.md)。

## 🗺️ 完整流程

| # | 节点 | 工具 |
|---|---|---|
| 0 | 按账号/关键词/指定素材采集，核实指标与范围 | blogger-video-pipeline；TikTok 默认 TikSave + `tiktok_assets.py` 复核 |
| 1 | 拆爆款结构 S1…Sn | `transcribe.py` `ref_compare.py` |
| 2 | 扫素材 + 打标签 | `scan.py` `summary.py` `tag_sheet.py` |
| 3 | 每个结构写一份文案（先对素材） | `overlap_check.py` |
| 4 | 口播（AI / 真人） | `tts_edge.py` `voice_prep.py` `voice_splice.py` `voice_speed.py` |
| 5 | 分镜 | `plan_beats.py` `coverage.py` |
| 6 | 配镜头 + 调色 + 字幕按实际字宽分屏 | `match.py` `grade.py` `caption_layout.py` |
| 7 | 出片（MP4 + 剪映草稿） | `render.py` |
| 8 | 自检时长、动态模式、字幕宽度、镜头与来源 | `qa.py` `ref_compare.py` `shot_stats.py`；成片动态区间需复看 |
| 9 | 批次清单 | `batch_list.py` |

每一步的输入输出、规则和踩过的坑见 [docs/流程SOP.html](docs/流程SOP.html)。

预览确认后说“再出10条”，保留原成片并继续编号，每条安排不同的钩子、卖点顺序与对应镜头。原参考数与成片数分别记录；少量参考改成多条时标清变体，不虚增对标数量。交付 MP4、剪映草稿与全部引用素材、字幕、中外文对照、逐镜来源和批次清单，多条提供统一预览入口。

TikTok 使用 [TikSave 无水印下载流程](docs/TikTok无水印下载-TikSave.md)：在指定浏览器下载真实文件，再用 `tools/tiktok_assets.py` 登记来源、生成检查帧、记录人工复核。必须通过水印检查才入剪；TikTok 标志/账号与原作者烧录字幕分开处理。网页下载需要实际取得 MP4。队列与本地复核工具已提供，当前未完成 TikSave 端到端下载验证。采用备用来源时，单独记录实际下载方式。

## ❓ 常见问题

- **出片报 `x264 malloc failed`**：电脑内存不够，关掉浏览器标签等占内存的程序再跑；4K 素材先缩到 1080p
- **剪映里看不到新草稿**：要先完全退出剪映（托盘也退），再双击 `安装到剪映.cmd`
- **AI 配音报 403**：`pip install -U edge-tts`
- **音效没声音**：运行 `python tools/get_sfx.py` 补下载
- **配置了角标但看不见**。检查 PNG 是否有透明背景、商品是否可见，再核对角标位置和宽度。
- **只有主页和白底产品图能开始吗**：可以先识别商品和采集该账号；缺少的功效、门槛、时长等再补问。不会擅自改为全网关键词采集。
- **外语字幕被切掉或画面像幻灯片**：字幕由 `caption_layout.py` 测宽分屏；定制字号同步测量。要求全动态时填写 `画面模式: "全动态"`，再复看是否存在已烘焙定格。

## ⭐ 支持项目

觉得有用就点个 Star；遇到问题或想要新功能，欢迎提 [Issue](https://github.com/caodoris471/viral-video-remix/issues)。

## 🙏 致谢

[pyJianYingDraft](https://github.com/GuanYixuan/pyJianYingDraft) · [faster-whisper](https://github.com/SYSTRAN/faster-whisper) · [RapidOCR](https://github.com/RapidAI/RapidOCR) · [edge-tts](https://github.com/rany2/edge-tts) · [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) · [Mixkit](https://mixkit.co)

## 📄 许可

Mixkit 音效配乐遵循 [Mixkit License](https://mixkit.co/license/)，由每台电脑自己从官网下载，本仓库不转发素材文件。
