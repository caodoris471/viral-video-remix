"""口播提速 + 润色：不变调加速，去低频噪声、轻降噪、提一点清晰度、压缩让音量更稳，并把时间戳按倍速换算。

用法: python voice_speed.py <口播目录(含 口播_精剪.wav, timestamps.json)> <输出目录> <倍速，如 1.15>
产物: 输出目录/口播_精剪.wav、timestamps.json
"""
from pathlib import Path
import json, subprocess, sys

src, out, k = Path(sys.argv[1]), Path(sys.argv[2]), float(sys.argv[3])
out.mkdir(parents=True, exist_ok=True)
chain = ",".join([
    "highpass=f=80",                       # 去掉空调、桌面震动等低频
    "afftdn=nf=-28",                       # 轻度降噪
    f"atempo={k}",                         # 不变调提速
    "equalizer=f=250:t=q:w=1.0:g=-2",      # 减一点闷
    "equalizer=f=3500:t=q:w=1.2:g=2.5",    # 提一点咬字清晰度
    "acompressor=threshold=-20dB:ratio=3:attack=5:release=80:makeup=2",
    "alimiter=limit=0.95",
])
wav = out / "口播_精剪.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src / "口播_精剪.wav"), "-af", chain, "-ar", "48000", "-ac", "1", str(wav)],
               check=True)
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(wav)]))
ts = json.loads((src / "timestamps.json").read_text(encoding="utf-8"))
r = lambda t: round(t / k, 3)
for s in ts["sentences"]:
    s["start"], s["end"] = r(s["start"]), r(s["end"])
    for w in s["words"]:
        w["start"], w["end"] = r(w["start"]), r(w["end"])
ts.update(source=f"{src / '口播_精剪.wav'} ×{k} 提速+润色", duration=round(dur, 3))
(out / "timestamps.json").write_text(json.dumps(ts, ensure_ascii=False, indent=1), encoding="utf-8")
chars = sum(len(s["words"]) for s in ts["sentences"])
print(f"{dur:.1f}s，语速 {chars / dur:.1f} 单位/秒（原 {chars / (dur * k):.1f}；中文是字，英语等是词）")
