"""项目整体搬家后，把文本文件里写死的旧路径换成新路径（/、\、JSON 转义的 \\ 三种写法都换）。
用法: python repath.py <扫描目录> <旧前缀> <新前缀> [--dry]
"""
from pathlib import Path
import sys

root, old, new = Path(sys.argv[1]), sys.argv[2].rstrip("\\/"), sys.argv[3].rstrip("\\/")
dry = "--dry" in sys.argv
variants = {}
for sep in ("/", "\\", "\\\\"):
    variants[old.replace("\\", "/").replace("/", sep)] = new.replace("\\", "/").replace("/", sep)
total = 0
for f in root.rglob("*"):
    if f.suffix.lower() not in {".json", ".py", ".md", ".txt", ".cmd"} or not f.is_file():
        continue
    raw = f.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        continue
    n = sum(text.count(k) for k in variants)
    if not n:
        continue
    for k, v in variants.items():
        text = text.replace(k, v)
    total += n
    print(f"{n:4d}  {f.relative_to(root)}")
    if not dry:
        f.write_bytes((b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8"))
print("合计替换", total, "处", "(dry run)" if dry else "")
