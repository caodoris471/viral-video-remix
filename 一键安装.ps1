# 实拍混剪 SOP 底座 一键安装（Windows 10/11）
# 用法：右键「一键安装.cmd」以普通用户运行即可
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
function Step($m) { Write-Host "`n==> $m" -ForegroundColor Cyan }
function Have($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }

Step "1/5 检查 Python 3.10+"
if (-not (Have python)) {
  if (Have winget) { winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements }
  else { throw "没有 Python，也没有 winget。请手动装 https://www.python.org/downloads/ ，勾选 Add to PATH 后重跑。" }
  $env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")
}
python --version

Step "2/5 检查 ffmpeg"
if (-not (Have ffmpeg)) {
  if (Have winget) { winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements }
  else { throw "没有 ffmpeg。请手动装 https://www.gyan.dev/ffmpeg/builds/ 并加入 PATH。" }
  $env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")
}
ffmpeg -version | Select-Object -First 1

Step "3/5 安装 Python 依赖（国内网络自动走清华镜像）"
python -m pip install -U pip -i https://pypi.tuna.tsinghua.edu.cn/simple
python -m pip install -r "$here\requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple

Step "4/5 安装浏览器驱动（抖音采集用，可失败）"
try { python -m playwright install msedge } catch { Write-Host "跳过：不采集抖音可忽略" -ForegroundColor Yellow }

Step "5/5 检查字体和剪映"
$font = "$env:LOCALAPPDATA\Microsoft\Windows\Fonts\HYYakuHei-95W.ttf"
if (Test-Path $font) { Write-Host "花字字体 OK" } else { Write-Host "缺花字字体 汉仪雅酷黑95W：预览会退回微软雅黑。装好后或设环境变量 MIX_KWFONT 指向你的字体。" -ForegroundColor Yellow }
$jy = "$env:LOCALAPPDATA\JianyingPro\User Data\Projects\com.lveditor.draft\root_meta_info.json"
if (Test-Path $jy) { Write-Host "剪映 OK" } else { Write-Host "没找到剪映专业版草稿索引：先装剪映并打开一次。" -ForegroundColor Yellow }

Step "自检"
python -c "import cv2, numpy, rapidocr_onnxruntime, faster_whisper, pyJianYingDraft, edge_tts; print('依赖全部可导入')"
Write-Host "`n安装完成。在 Codex / Claude Code 里说：用 real-footage-montage 帮我做一批混剪" -ForegroundColor Green
Write-Host "音效库为空也能出片；想要音效见 音效库\README.md" -ForegroundColor Green
