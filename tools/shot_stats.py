"""排查“为什么不顺”：逐段量 源帧率、平均亮度、饱和度、色温倾向，看相邻镜头跳多少。
用法: python shot_stats.py <项目目录> <EDL 文件名>
"""
from pathlib import Path
import json, re, subprocess, sys

proj = Path(sys.argv[1])
cfg = json.loads((proj / "config.json").read_text(encoding="utf-8"))
edl = json.loads((proj / "work" / sys.argv[2]).read_text(encoding="utf-8"))
lib = Path(cfg["素材目录"])
rows = []
for s in edl["镜头"]:
    if s.get("占位"):
        continue
    f = lib / s["源文件"]
    fps = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                                   "-of", "csv=p=0", str(f)]).decode().strip()
    n, d = map(float, fps.split("/"))
    c = s["裁切"]
    err = subprocess.run(["ffmpeg", "-hide_banner", "-ss", str(s["源入点"]), "-t", str(s["止"] - s["起"]), "-i", str(f), "-vf",
                          f"crop=iw*{c['w']}:ih*{c['h']}:iw*{c['x0']}:ih*{c['y0']},scale=160:-2,signalstats,"
                          "metadata=print:file=-", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8",
                         errors="replace").stdout
    def avg(key):
        v = [float(x) for x in re.findall(rf"{key}=([\d.]+)", err)]
        return sum(v) / len(v) if v else 0
    y, sat, u, v = avg("lavfi.signalstats.YAVG"), avg("lavfi.signalstats.SATAVG"), avg("lavfi.signalstats.UAVG"), avg("lavfi.signalstats.VAVG")
    rows.append(dict(段=s["段"], 窗=s["窗"], fps=round(n / d, 2), 亮度=round(y), 饱和=round(sat), 暖=round(v - u)))
prev = None
for r in rows:
    jump = "" if prev is None else f"  跳变 亮{r['亮度'] - prev['亮度']:+d} 暖{r['暖'] - prev['暖']:+d}"
    print(f"段{r['段']:2d} {r['窗']:5s} {r['fps']:5.2f}fps 亮度{r['亮度']:3d} 饱和{r['饱和']:3d} 暖{r['暖']:+4d}{jump}")
    prev = r
fpss = sorted({r["fps"] for r in rows})
print("源帧率种类:", fpss, "| 成片 30fps")
print("相邻亮度跳变 >40 的切点:", sum(abs(a["亮度"] - b["亮度"]) > 40 for a, b in zip(rows, rows[1:])))
