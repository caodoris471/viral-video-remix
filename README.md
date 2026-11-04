# 实拍混剪自动化 · real-footage-montage

把实拍素材和口播自动混剪成 9:16 种草/带货短视频：扫素材 → 避字幕自动裁切 → 按台词配镜头 → 花字大字 → 出预览 MP4 和**剪映草稿**（可直接微调）。

- **多语言 AI 口播**：16 种语言，每种内置热门男声/女声（edge-tts，免费）；也支持真人录音（自动剪口误、压停顿、提速）
- **一批多条、按爆款结构编号**：每条成片对应一个爆款结构 S1…Sn，自动生成批次清单，发布后填数据就能比较哪种结构有效
- **采集不限平台**：配合 [blogger-video-pipeline](https://github.com/caodoris471/blogger-video-pipeline)（抖音/小红书/视频号/B站/快手/YouTube/TikTok/Instagram）
- Codex 和 Claude Code 都能用

## 一句话安装

把这段话发给 Codex 或 Claude Code：

```
帮我安装这个 skill：https://github.com/caodoris471/real-footage-montage
把它 git clone 到你的 skills 目录（Codex 是 ~/.codex/skills，Claude Code 是 ~/.claude/skills），文件夹名 real-footage-montage；然后运行里面的 一键安装.ps1，装完告诉我哪些通过、哪些要我手动处理。
采集对标用的 skill 也一起装：https://github.com/caodoris471/blogger-video-pipeline
```

装完开新对话说：`用 real-footage-montage 帮我做一批混剪`。

手动安装、需要替换的信息见 [docs/安装底座.html](docs/安装底座.html)；完整流程见 [docs/流程SOP.html](docs/流程SOP.html)（下载后用浏览器打开）。

## 流程

| # | 节点 | 工具 |
|---|---|---|
| 0 | 采集对标 + 下载原片 | blogger-video-pipeline |
| 1 | 拆爆款结构 S1…Sn | `transcribe.py` `ref_compare.py` |
| 2 | 扫素材 + 打标签 | `scan.py` `summary.py` `tag_sheet.py` |
| 3 | 每个结构写一份文案（先对素材） | `overlap_check.py` |
| 4 | 口播（AI / 真人） | `tts_edge.py` `voice_prep.py` `voice_splice.py` `voice_speed.py` |
| 5 | 分镜 | `plan_beats.py` `coverage.py` |
| 6 | 配镜头 + 调色 | `match.py` `grade.py` |
| 7 | 出片（MP4 + 剪映草稿） | `render.py` |
| 8 | 自检 | `qa.py` `ref_compare.py` `shot_stats.py` |
| 9 | 批次清单 | `batch_list.py` |

## 环境

Windows 10/11 · Python 3.10+ · ffmpeg · 剪映专业版。`一键安装.ps1` 会自动装缺的部分。

音效和配乐因许可原因不随仓库分发，见 [音效库/README.md](音效库/README.md)。

## 致谢

剪映草稿生成基于 [pyJianYingDraft](https://github.com/GuanYixuan/pyJianYingDraft)；语音识别 faster-whisper；字幕识别 RapidOCR；配音 edge-tts。
