"""第4.5步 统一亮度：量每个镜头取用片段的平均亮度/饱和度，把偏亮、偏暗的拉向全片中位数一半，写进 EDL 的“调色”。
（素材来自很多作者，亮度跳来跳去是“看着不顺”的主要原因之一；只拉一半，保留每个镜头本来的氛围）
用法: python grade.py <项目目录> <EDL 文件名>
"""
from pathlib import Path
import json, re, statistics, subprocess, sys

proj = Path(sys.argv[1])
cfg = json.loads((proj / "config.json").read_text(encoding="utf-8"))
p = proj / "work" / sys.argv[2]
edl = json.loads(p.read_text(encoding="utf-8"))
lib = Path(cfg["素材目录"])
stats = {}
for s in edl["镜头"]:
    if s.get("占位"):
        continue
    c = s.get("宽裁切") or s["裁切"]
    out = subprocess.run(["ffmpeg", "-hide_banner", "-ss", str(s["源入点"]), "-t", str(s["止"] - s["起"]), "-i", str(lib / s["源文件"]),
                          "-vf", f"fps=5,crop=iw*{c['w']}:ih*{c['h']}:iw*{c['x0']}:ih*{c['y0']},scale=128:-2,signalstats,"
                          "metadata=print:file=-", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8",
                         errors="replace").stdout
    y = [float(v) for v in re.findall(r"YAVG=([\d.]+)", out)]
    sat = [float(v) for v in re.findall(r"SATAVG=([\d.]+)", out)]
    stats[s["段"]] = (statistics.mean(y) if y else 110, statistics.mean(sat) if sat else 20)
my = statistics.median(v[0] for v in stats.values())
ms = statistics.median(v[1] for v in stats.values())
for s in edl["镜头"]:
    if s["段"] not in stats:
        continue
    y, sat = stats[s["段"]]
    b = max(-0.12, min(0.12, (my - y) / 2 / 255))           # 亮度只拉一半，最多 ±0.12
    k = max(0.85, min(1.2, 1 + (ms - sat) / 2 / max(ms, 1)))  # 饱和度同理
    s["调色"] = f"brightness={b:.3f}:saturation={k:.3f}"
    print(f"段{s['段']:2d} 亮度{y:5.0f}→{y + b * 255:5.0f} 饱和{sat:4.0f}×{k:.2f}")
p.write_text(json.dumps(edl, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"全片中位亮度 {my:.0f}，饱和 {ms:.0f}")
