"""口播排查：打印某句的逐字时间和该时间段每 0.25 秒的音量，找没压掉的停顿。
用法: python voice_inspect.py <口播目录(含 口播_精剪.wav, timestamps.json)> <句号(从1开始)>
"""
from pathlib import Path
import json, subprocess, sys
import numpy as np

d, n = Path(sys.argv[1]), int(sys.argv[2])
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(d / "口播_精剪.wav"), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                     capture_output=True).stdout
x = np.frombuffer(raw, np.float32)
w = 4000
db = [20 * np.log10(np.sqrt((x[i:i + w] ** 2).mean()) + 1e-9) for i in range(0, len(x) - w, w)]
print(f"底噪 p10 {np.percentile(db, 10):.0f} dB，说话 p90 {np.percentile(db, 90):.0f} dB")
s = json.loads((d / "timestamps.json").read_text(encoding="utf-8"))["sentences"][n - 1]
print(f"第{n}句 {s['start']}–{s['end']}：{s['text']}")
print(" ".join(f"{w['word']}{w['start']:.2f}" for w in s["words"]))
seg = [(i * 0.25, round(v)) for i, v in enumerate(db) if s["start"] - 0.3 <= i * 0.25 <= s["end"] + 0.3]
print("音量:", " ".join(f"{t:.2f}:{v}" for t, v in seg))
