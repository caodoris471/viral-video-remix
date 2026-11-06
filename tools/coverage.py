"""配镜头前的覆盖检查：每段有多少合格窗（不停在第一个缺口，一次列全）。
用法: python coverage.py <项目目录> <分镜文件名>
"""
from pathlib import Path
import sys
from common import load, sentences, beat_times, tagged_pool

proj = Path(sys.argv[1])
cfg = load(proj / "config.json")
beats = load(proj / sys.argv[2])
cands = load(proj / "work/candidates.json")["窗"]
tags = load(proj / "work/tags.json")
pool = tagged_pool(cands, tags, cfg)
ss = sentences(beats)
for i, (b, (a, e)) in enumerate(zip(beats["段"], beat_times(beats, cfg))):
    if "用图" in b:
        print(f"段{i + 1} {e - a:.2f}s 用户原图")
        continue
    need = set(b["必需"])
    has_tag = [c for c in pool if need <= set(c["标签"])]
    ok = [c for c in has_tag if c["时长"] >= e - a]
    text = "".join(ss[k]["text"] for k in b["句"])
    print(f"段{i + 1} {e - a:.2f}s 需{sorted(need)} 合格{len(ok)} {[c['id'] for c in ok]}"
          + (f" | 有标签但太短: {[(c['id'], c['时长']) for c in has_tag if c not in ok]}" if len(ok) < len(has_tag) else "")
          + f"  《{text}》")
