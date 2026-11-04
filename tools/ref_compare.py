"""对标对照：量参考视频和我们成片的剪辑节奏，找差距。
指标：时长、帧率、切点数、镜头时长分布、切点前后亮度跳变；另出一张“每个切点前后各一帧”的对照图。
用法: python ref_compare.py <输出目录> <视频1> [视频2 ...]
"""
from pathlib import Path
import re, statistics, subprocess, sys

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)


def probe(f, key):
    return subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", key, "-of", "csv=p=0",
                                    str(f)]).decode().strip()


for f in map(Path, sys.argv[2:]):
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)]))
    n, d = map(float, probe(f, "stream=r_frame_rate").split("/"))
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(f), "-vf", "scale=160:-2,select='gt(scene,0.25)',showinfo", "-f",
                          "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    cuts = []
    for t in (float(x) for x in re.findall(r"pts_time:([\d.]+)", err)):
        if not cuts or t - cuts[-1] > 0.3:
            cuts.append(t)
    lens = [b - a for a, b in zip([0, *cuts], [*cuts, dur])]
    y = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(f), "-vf", "fps=10,scale=96:-2,signalstats,metadata=print:file=-",
                        "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    ys = [float(v) for v in re.findall(r"YAVG=([\d.]+)", y)]
    jumps = [abs(ys[min(len(ys) - 1, int(c * 10) + 1)] - ys[max(0, int(c * 10) - 1)]) for c in cuts] if ys else []
    print(f"== {f.name[:40]}")
    print(f"  {dur:.1f}s {n / d:.0f}fps 切点 {len(cuts)} 个，每秒 {len(cuts) / dur:.2f} 刀")
    print(f"  镜头时长 中位 {statistics.median(lens):.2f}s 最短 {min(lens):.2f}s 最长 {max(lens):.2f}s")
    if jumps:
        print(f"  切点亮度跳变 中位 {statistics.median(jumps):.0f} 最大 {max(jumps):.0f}，>40 的 {sum(j > 40 for j in jumps)} 个")
    sel = "+".join(f"eq(n\\,{max(0, round(c * n / d) - 2)})+eq(n\\,{round(c * n / d) + 2})" for c in cuts[:12])
    if sel:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(f), "-vf", f"select='{sel}',scale=150:-2,tile=8x3",
                        "-frames:v", "1", str(out / f"切点_{f.stem[:12]}.png")])
