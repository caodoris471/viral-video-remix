# TikTok 无水印下载：TikSave

TikTok 原片默认用用户指定的 [TikSave](https://tiksave.io/zh-cn)，在用户指定的浏览器中操作。它是网页下载服务，不是本机已安装的去字幕插件。采集工具继续负责搜索、热度、作者、原链接与平台 ID；TikSave 负责获取不带平台水印的候选原片。

## 必须区分

- **平台水印**：TikTok 标志和随时间移动的 `@作者账号`。先换无水印源，不能直接用大幅裁切或上下模糊作为默认解法。
- **烧录字幕**：原作者加进画面的英文文案、标题、贴纸。无水印下载不保证去掉这些文字；需要时另走 [视频字幕擦除工具接入](视频字幕擦除工具接入.md)。
- 作者、平台 ID、原链接、固定素材编号仍保存在本地清单和飞书，下载版本变化不重新编号。

## 执行流程

1. 先采集并筛选对标，保存 JSON 数组，每条至少有 `source_number`、字符串 `id`、`url`、`author`。`url` 为公开的 `https://www.tiktok.com/@作者/video/视频ID`。
2. 准备下载队列：

   ```powershell
   python tools/tiktok_assets.py prepare --sources "<素材清单.json>" --out "<项目执行目录>/tiktok_downloads"
   ```

3. 在当前会话提供的浏览器工具中操作 TikSave；用户指定 Chrome 时使用 Chrome。打开 `https://tiksave.io/zh-cn`，将队列中的单条公开 TikTok 链接填入页面输入框，点击页面上的下载按钮，等待结果。只点击实际显示的视频/无水印下载控件，不点击广告或安装软件入口。不猜测私有 API，不将 Cookie、凭证或私密视频传给该服务。
4. 根据当时页面状态选择无水印 MP4；确认结果与原片内容、作者/平台 ID 对应，保存结果截图。通过浏览器支持的下载能力获取文件；下载后将原片放入项目的素材目录。网页宣称“无水印”或出现成功按钮，都不能代替实际文件验收。
5. 登记真实下载文件并生成 6 张覆盖开头、中段、结尾的检查帧：

   ```powershell
   python tools/tiktok_assets.py register --out "<项目执行目录>/tiktok_downloads" --id "<视频ID>" --file "<真实下载.mp4>" --evidence "<TikSave结果截图.png>"
   ```

6. 查看输出的 `watermark_review.jpg`，并播放/抽查实际将要使用的镜头区间，检查上下左右移动位置和结尾标志；核对内容、时长、主体完整性及有无 TikTok 标志或账号。确实通过才能执行：

   ```powershell
   python tools/tiktok_assets.py review --out "<项目执行目录>/tiktok_downloads" --id "<视频ID>" --decision passed --note "<实际检查的位置、时间段及结果>"
   python tools/tiktok_assets.py verify --out "<项目执行目录>/tiktok_downloads" --ids "<视频ID>"
   ```

   有水印或内容不对应则用 `--decision failed`。脚本只核验文件、媒体参数与人工检查记录，不会自动判断所有帧无水印；不能未看图就填 passed。`manifest.json` 记录来源、固定编号、下载时间、文件哈希、结果截图及复核状态。
7. 只把已通过复核的文件交给扫素材、字幕清理和混剪。替换旧素材时保留旧版与来源映射，先检查新旧版本的时长、入点、出点；重导出后再看成片是否重新带入旧水印源。

## 失败与回退

- 页面无法解析、下载失败、出现验证或浏览器控制被停止时，记录具体原因；不得把状态改为下载成功，不得静默回到带水印下载源。遵从当前工具的验证/用户接管规则，不自行绕过。
- TikSave 不可用时明确告知。需要采用其他下载方式时说明实际来源；yt-dlp 只能作为明确说明的备用，不再使用 `download/...` 优先选择器。备用候选至少排除 `format_note` 含 `watermark` 以及已知带水印的 `format_id=download`；仍需实际抽帧检查，格式名称不等于无水印证明。
- 不覆盖已交付原片，不将旧文件存在或 HTTP 成功当成新版通过。只有成功下载且通过视觉复核才更新飞书的下载方式/水印状态和成片素材路径。

## 当前验证范围

本包提供网页操作说明，以及建队列、文件登记、抽帧和人工复核工具。TikSave 端到端下载尚未验证。网页能打开时仍需实际取得并检查 MP4，再登记通过。
