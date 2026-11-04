"""打印扫描结果概况：不可用原因统计、可用窗清单。用法: python summary.py <项目目录>"""
from pathlib import Path
import collections, sys
from common import load

d = load(Path(sys.argv[1]) / "work/candidates.json")["窗"]
print("不可用原因:", collections.Counter(w.get("原因", "")[:14] for w in d if not w.get("可用")).most_common())
ok = [w for w in d if w.get("可用")]
print(f"可用 {len(ok)} 个:")
for w in ok:
    print(f"  {w['id']} {w['源文件'][:19]} {w['入']:6.1f}-{w['出']:6.1f} {w['时长']:.1f}s 动{w['运动量']:.1f} {w['裁切像素宽']}px")
