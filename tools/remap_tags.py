"""重扫后窗号变了（如改了最短镜头秒，窗被重新切分）时，把旧标签按“同一原片 + 时间重叠”搬到新窗上。
新窗有 ≥80% 落在某个旧窗里，就继承那个旧窗的标签；搬不过去的新窗留空（不打标签 = 匹配时不用），需要再看图补。
用法: python remap_tags.py <work 目录>   （读 candidates_备份_宽裁切前.json + tags_备份_宽裁切前.json）
"""
from pathlib import Path
import json, sys

w = Path(sys.argv[1])
old = json.loads((w / "candidates_备份_宽裁切前.json").read_text(encoding="utf-8"))["窗"]
old_tags = json.loads((w / "tags_备份_宽裁切前.json").read_text(encoding="utf-8"))
new = json.loads((w / "candidates.json").read_text(encoding="utf-8"))["窗"]
by_src = {}
for c in old:
    if c["id"] in old_tags:
        by_src.setdefault(c["源文件"], []).append(c)
tags, moved, left = {}, 0, []
for c in new:
    best, best_ov = None, 0.0
    for o in by_src.get(c["源文件"], []):
        ov = max(0.0, min(c["出"], o["出"]) - max(c["入"], o["入"]))
        if ov > best_ov:
            best, best_ov = o, ov
    if best and best_ov >= 0.8 * c["时长"]:
        tags[c["id"]] = old_tags[best["id"]]
        moved += 1
    elif c.get("可用"):
        left.append(c["id"])
(w / "tags.json").write_text(json.dumps(tags, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"旧标签 {len(old_tags)} 条 → 新窗继承 {moved} 条；可用但没继承到的新窗 {len(left)} 个（不参与匹配）")
print("没继承到的:", " ".join(left[:40]))
