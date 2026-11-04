"""第1步 扫素材：切点 → 可用窗 → OCR 找烧录字 → 自动算避字裁切窗 → 窗内运动量 → 联系表。

用法: python scan.py <项目目录>
输出: <项目>/work/candidates.json, <项目>/work/sheets/sheet_XX.png
"""
from pathlib import Path
import json, re, subprocess, sys
import cv2
import numpy as np

SMALL = (144, 256)        # 运动量计算用灰度小图 (w, h)
OCR_W = 540               # OCR 用图宽
THUMB = (120, 213)


def scene_cuts(path, thr):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-vf",
                          f"scale=270:-2,select='gt(scene,{thr})',showinfo", "-f", "null", "-"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    cuts = []
    for t in (float(m) for m in re.findall(r"pts_time:([\d.]+)", err)):
        if not cuts or t - cuts[-1] > 0.3:
            cuts.append(t)
    return cuts


def read_video(path, ocr, ocr_every):
    """顺序读一遍：每帧存灰度小图；每隔 ocr_every 秒做一次文字检测并存缩略 JPEG。"""
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    step = max(1, round(fps * ocr_every))
    small, samples, i = [], [], 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        h, w = f.shape[:2]
        small.append(cv2.cvtColor(cv2.resize(f, SMALL, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY))
        if i % step == 0:
            g = cv2.resize(f, (OCR_W, round(OCR_W * h / w)), interpolation=cv2.INTER_AREA)
            failed = False
            try:
                boxes, _ = ocr(g, use_det=True, use_cls=False, use_rec=False)
            except Exception:   # 内存紧张时 onnxruntime 偶发 bad allocation：缩小一半重试，再失败就记为检测失败
                try:
                    g2 = cv2.resize(g, (OCR_W // 2, g.shape[0] // 2))
                    boxes, _ = ocr(g2, use_det=True, use_cls=False, use_rec=False)
                    boxes = [[[p[0] * 2, p[1] * 2] for p in b] for b in (boxes or [])]
                except Exception:
                    boxes, failed = [], True
            gh, gw = g.shape[:2]
            norm = [(min(p[0] for p in b) / gw, min(p[1] for p in b) / gh, max(p[0] for p in b) / gw, max(p[1] for p in b) / gh)
                    for b in (boxes or [])]
            samples.append(dict(t=i / fps, boxes=norm, failed=failed, jpg=cv2.imencode(".jpg", g, [cv2.IMWRITE_JPEG_QUALITY, 85])[1],
                                row=g.mean(axis=(1, 2)), col=g.mean(axis=(0, 2))))
        i += 1
    cap.release()
    return fps, w, h, np.stack(small), samples


def content_box(samples):
    """黑边：90 分位亮度 < 16 的行/列视为黑边。"""
    def span(arr):
        v = np.percentile(np.stack(arr), 90, axis=0)
        idx = np.where(v > 16)[0]
        return (idx[0] / len(v), (idx[-1] + 1) / len(v)) if len(idx) else (0.0, 1.0)
    x0, x1 = span([s["col"] for s in samples])
    y0, y1 = span([s["row"] for s in samples])
    return x0, y0, x1, y1


def best_crop(boxes, cb, src_w, src_h, out_aspect, pad):
    """在内容区内找最大的、不碰任何文字框的 out_aspect 窗；同尺寸取离内容中心最近的位置。"""
    cx0, cy0, cx1, cy1 = cb
    bx = np.array([(b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad) for b in boxes]) if boxes else np.zeros((0, 4))
    r = (src_w / src_h) / out_aspect          # 归一化高 = 归一化宽 * r
    for wn in np.arange(min(cx1 - cx0, (cy1 - cy0) / r), 0.2, -0.01):
        hn = wn * r
        xs = np.linspace(cx0, cx1 - wn, 25)
        ys = np.linspace(cy0, cy1 - hn, 25)
        X, Y = np.meshgrid(xs, ys)
        X, Y = X.ravel(), Y.ravel()
        ok = np.ones(len(X), bool)
        for b in bx:
            ok &= ~((X < b[2]) & (X + wn > b[0]) & (Y < b[3]) & (Y + hn > b[1]))
        if ok.any():
            d = (X + wn / 2 - (cx0 + cx1) / 2) ** 2 + (Y + hn / 2 - (cy0 + cy1) / 2) ** 2
            k = np.where(ok)[0][np.argmin(d[ok])]
            return float(X[k]), float(Y[k]), float(wn), float(hn)
    return None


def file_ids(proj, files):
    """素材编号固定不变：记在 work/file_ids.json。老素材保持原字母，新素材接着往后排。
    （以前按文件名排序给字母，加新素材会让老素材改号，已打的标签就对不上了。）"""
    p = Path(proj) / "work" / "file_ids.json"
    ids = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    if not ids:   # 首次：沿用旧规则（排序后 A、B、C…），与已有扫描缓存和标签一致
        ids = {f.name: chr(ord("A") + i) for i, f in enumerate(sorted(files))}
    used = set(ids.values())
    AZ = [chr(c) for c in range(ord("A"), ord("Z") + 1)]
    codes = AZ + [a + b for a in AZ for b in AZ]   # A…Z 用完接 AA、AB…（窗号 = 字母 + 两位数字，如 AA03）
    for f in sorted(files):
        if f.name not in ids:
            letter = next(c for c in codes if c not in used)
            ids[f.name] = letter
            used.add(letter)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(ids, ensure_ascii=False, indent=1), encoding="utf-8")
    return ids


def scan_one(proj, name):
    """扫一条素材，结果写进 work/scan_cache/（单独进程跑，内存用完即释放；已扫过的不重扫）。"""
    proj = Path(proj)
    cfg = json.loads((proj / "config.json").read_text(encoding="utf-8"))
    R = cfg["规则"]
    out_aspect = cfg["画布"]["宽"] / cfg["画布"]["高"]
    cache = proj / "work" / "scan_cache"
    cache.mkdir(parents=True, exist_ok=True)
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR()
    f = Path(cfg["素材目录"]) / name
    cands = []
    if True:
        letter = file_ids(proj, sorted(Path(cfg["素材目录"]).glob("*.mp4")))[name]
        fps, sw, sh, small, samples = read_video(f, ocr, R["OCR采样间隔秒"])
        dur = len(small) / fps
        cuts = scene_cuts(f, R["切点阈值"])
        cb = tuple(float(v) for v in content_box(samples))
        edges = [0.0, *cuts, dur]
        n = 0
        for a, b in zip(edges, edges[1:]):
            a, b = a + R["镜头窗边距秒"], b - R["镜头窗边距秒"]
            if b - a < R["最短镜头秒"]:
                continue
            k = max(1, int((b - a) // R["长镜头拆窗秒"]))
            step = (b - a) / k
            for j in range(k):
                wa, wb = a + j * step, a + (j + 1) * step
                inside = [s for s in samples if wa - 0.05 <= s["t"] <= wb + 0.05]
                boxes = [bx for s in inside for bx in s["boxes"] if bx[3] - bx[1] >= R["文字最小高度"]]
                crop = best_crop(boxes, cb, sw, sh, out_aspect, R["文字外扩"])
                n += 1
                cid = f"{letter}{n:02d}"
                row = dict(id=cid, 源文件=f.name, 源宽=sw, 源高=sh, 入=round(wa, 3), 出=round(wb, 3), 时长=round(wb - wa, 3),
                           内容区=[round(v, 3) for v in cb], 文字框数=len(boxes))
                if any(s["failed"] for s in inside):
                    row.update(可用=False, 原因="文字检测失败（内存不足），宁可不用，避免漏掉原字幕")
                    cands.append(row)
                    continue
                if crop is None:
                    row.update(可用=False, 原因="找不到避开文字的裁切窗")
                    cands.append(row)
                    continue
                x0, y0, wn, hn = crop
                px = round(wn * sw)
                fa, fb = round(wa * fps), round(wb * fps)
                g = small[fa:fb, int(y0 * SMALL[1]):int((y0 + hn) * SMALL[1]), int(x0 * SMALL[0]):int((x0 + wn) * SMALL[0])].astype(np.int16)
                mot = float(np.abs(np.diff(g, axis=0)).mean()) if len(g) > 1 else 0.0
                row.update(裁切=dict(x0=round(x0, 4), y0=round(y0, 4), w=round(wn, 4), h=round(hn, 4)), 裁切像素宽=px,
                           运动量=round(mot, 2), 可用=px >= R["裁切最小像素宽"],
                           原因="" if px >= R["裁切最小像素宽"] else f"裁切后只剩 {px}px 宽，放大太多")
                # 宽裁切：更宽的避字窗（宽高比 4:5），出片时放在画面中间，上下用同一镜头的模糊放大版补满（对标视频的做法），
                # 比 9:16 窄裁放大清楚得多
                wide = best_crop(boxes, cb, sw, sh, R.get("宽裁切宽高比", 0.8), R["文字外扩"])
                if wide and round(wide[2] * sw) > px:
                    row.update(宽裁切=dict(x0=round(wide[0], 4), y0=round(wide[1], 4), w=round(wide[2], 4), h=round(wide[3], 4)),
                               宽裁切像素宽=round(wide[2] * sw))
                cands.append(row)
                if True:   # 有裁切窗就存缩略图；“可用”由阈值决定，改阈值不必重扫
                    picks = [inside[0], inside[len(inside) // 2], inside[-1]] if inside else []
                    tiles = []
                    for s in picks:
                        img = cv2.imdecode(s["jpg"], cv2.IMREAD_COLOR)
                        ih, iw = img.shape[:2]
                        c = img[int(y0 * ih):int((y0 + hn) * ih), int(x0 * iw):int((x0 + wn) * iw)]
                        tiles.append(cv2.resize(c, THUMB, interpolation=cv2.INTER_AREA))
                    strip = np.hstack(tiles)
                    cv2.rectangle(strip, (0, 0), (strip.shape[1], 18), (0, 0, 0), -1)
                    cv2.putText(strip, f"{cid} {wb - wa:.1f}s m{mot:.1f} {px}px", (3, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
                    (cache / f"{cid}.png").write_bytes(cv2.imencode(".png", strip)[1].tobytes())
        (cache / f"{letter}.json").write_text(json.dumps(cands, ensure_ascii=False), encoding="utf-8")
        print(f"{letter} {f.name} {sw}x{sh} {dur:.1f}s cuts={len(cuts)} 窗={n} 内容区={[round(v, 2) for v in cb]}", flush=True)


def main(proj):
    """逐条素材开子进程扫描（已缓存的跳过），再汇总 candidates.json 和联系表。"""
    proj = Path(proj)
    cfg = json.loads((proj / "config.json").read_text(encoding="utf-8"))
    work = proj / "work"
    cache = work / "scan_cache"
    (work / "sheets").mkdir(parents=True, exist_ok=True)
    files = sorted(Path(cfg["素材目录"]).glob("*.mp4"))
    ids = file_ids(proj, files)
    for f in files:
        if not (cache / f"{ids[f.name]}.json").exists():
            r = subprocess.run([sys.executable, __file__, str(proj), "--one", f.name])
            if r.returncode:
                print(f"{ids[f.name]} {f.name} 扫描失败（返回 {r.returncode}），跳过这条素材", flush=True)
    cands = []
    for f in sorted(files, key=lambda f: ids[f.name]):
        p = cache / f"{ids[f.name]}.json"
        if p.exists():
            cands += json.loads(p.read_text(encoding="utf-8"))
    min_px = cfg["规则"]["裁切最小像素宽"]
    for c in cands:   # 按当前配置重新判定清晰度，不必重扫
        if "裁切像素宽" in c and c.get("原因", "").startswith(("裁切后只剩", "")) and "检测失败" not in c.get("原因", "") \
                and "找不到" not in c.get("原因", ""):
            c["可用"] = c["裁切像素宽"] >= min_px
            c["原因"] = "" if c["可用"] else f"裁切后只剩 {c['裁切像素宽']}px 宽，放大太多"
    thumbs = [cv2.imdecode(np.fromfile(str(cache / f"{c['id']}.png"), np.uint8), cv2.IMREAD_COLOR) for c in cands if c.get("可用")]
    (work / "candidates.json").write_text(json.dumps(dict(素材=[f.name for f in files], 窗=cands), ensure_ascii=False, indent=1),
                                          encoding="utf-8")
    per_row, rows_per_sheet = 6, 5
    blank = np.zeros_like(thumbs[0]) if thumbs else None
    for s in range(0, len(thumbs), per_row * rows_per_sheet):
        chunk = thumbs[s:s + per_row * rows_per_sheet]
        rows = []
        for r in range(0, len(chunk), per_row):
            row = chunk[r:r + per_row]
            row += [blank] * (per_row - len(row))
            rows.append(np.hstack([np.pad(t, ((2, 2), (2, 2), (0, 0))) for t in row]))
        (work / "sheets" / f"sheet_{s // (per_row * rows_per_sheet) + 1:02d}.png").write_bytes(cv2.imencode(".png", np.vstack(rows))[1].tobytes())
    ok = [c for c in cands if c.get("可用")]
    print(f"窗总数 {len(cands)}，可用 {len(ok)}，联系表 {len(list((work / 'sheets').glob('*.png')))} 张")


if __name__ == "__main__":
    if len(sys.argv) > 3 and sys.argv[2] == "--one":
        scan_one(sys.argv[1], sys.argv[3])
    else:
        main(sys.argv[1])
