"""打标签辅助：把还没打标签的可用窗拼成联系表（每张 4×5），供人工看图打标签。
用法: python tag_sheet.py <项目目录> [字母前缀，如 NOPQ]
产物: work/tag_sheets/todo_XX.png、work/tag_sheets/todo.json（窗号、时长、运动量）
"""
from pathlib import Path
import json, sys
import cv2
import numpy as np

proj = Path(sys.argv[1])
pref = sys.argv[2] if len(sys.argv) > 2 else ""   # 素材编号，逗号分隔，如 X,Y,AA；不填 = 全部未打标签的窗
work = proj / "work"
cands = json.loads((work / "candidates.json").read_text(encoding="utf-8"))["窗"]
tags = json.loads((work / "tags.json").read_text(encoding="utf-8"))
todo = [c for c in cands if c.get("可用") and c["id"] not in tags and (not pref or c["id"].rstrip("0123456789") in pref.split(","))]
out = work / "tag_sheets"
out.mkdir(exist_ok=True)
for f in out.glob("todo_*.png"):
    f.unlink()
per = 20
for s in range(0, len(todo), per):
    imgs = []
    for c in todo[s:s + per]:
        im = cv2.imdecode(np.fromfile(str(work / "scan_cache" / f"{c['id']}.png"), np.uint8), cv2.IMREAD_COLOR)
        im = cv2.resize(im, (im.shape[1] * 2, im.shape[0] * 2), interpolation=cv2.INTER_CUBIC)
        cv2.rectangle(im, (0, 0), (im.shape[1], 30), (0, 0, 0), -1)
        cv2.putText(im, f"{c['id']} {c['时长']:.1f}s m{c.get('运动量', 0):.1f}", (4, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        imgs.append(np.pad(im, ((3, 3), (3, 3), (0, 0))))
    blank = np.zeros_like(imgs[0])
    imgs += [blank] * (-len(imgs) % 4)
    rows = [np.hstack(imgs[r:r + 4]) for r in range(0, len(imgs), 4)]
    p = out / f"todo_{s // per + 1:02d}.png"
    p.write_bytes(cv2.imencode(".png", np.vstack(rows))[1].tobytes())
    print(p.name, [c["id"] for c in todo[s:s + per]])
(out / "todo.json").write_text(json.dumps([dict(id=c["id"], 时长=c["时长"], 运动量=c.get("运动量")) for c in todo], ensure_ascii=False), encoding="utf-8")
print("待打标签", len(todo))
