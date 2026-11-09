"""批次清单：把一个项目里所有成片按爆款结构列成表，发布后在后面填播放/完播/互动数据做结构对比。

用法: python batch_list.py <项目目录>
产物: <项目>/批次清单.csv（Excel 可直接打开；可整表导入飞书多维表）
"""
from pathlib import Path
import csv, sys
from common import load

proj = Path(sys.argv[1])
rows = []
for f in sorted((proj / "output").glob("*/编辑决定表.json")):
    e = load(f)
    mp4 = next(f.parent.glob("*_预览.mp4"), None)
    text = "".join(c["文本"] for c in e["字幕"]) if e.get("语言", "zh") in ("zh", "ja") else " ".join(c["文本"] for c in e["字幕"])
    rows.append({"爆款结构": e.get("爆款结构") or "", "主结构对标": e.get("主结构对标") or "",
                 "结构主题": e.get("结构主题") or "", "结构改编": e.get("结构改编") or "",
                 "对标链接": e.get("对标链接") or "", "版本": e["版本"],
                 "草稿名": e["草稿名"], "语言": e.get("语言", "zh"), "时长秒": e["总时长"], "镜头数": len(e["镜头"]),
                 "文案": text, "成片": str(mp4 or ""), "发布平台": "", "发布链接": "", "播放": "", "完播率": "",
                 "点赞": "", "评论": "", "收藏": "", "转发": "", "结论": ""})
rows.sort(key=lambda r: (r["爆款结构"], r["版本"]))
out = proj / "批次清单.csv"
with open(out, "w", encoding="utf-8-sig", newline="") as fp:
    w = csv.DictWriter(fp, fieldnames=list(rows[0]) if rows else ["爆款结构"])
    w.writeheader()
    w.writerows(rows)
print(f"{len(rows)} 条 → {out}")
