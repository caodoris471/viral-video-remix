"""TikSave browser-download queue, local registration and visual-review gate.

No private API calls, browser bootstrap or CAPTCHA handling. The browser agent
downloads via the real TikSave page, then this helper handles local files.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

SERVICE = "https://tiksave.io/zh-cn"


def stamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source_row(folder, source_id):
    rows = read(Path(folder) / "queue.json")
    return next(r for r in rows if r["id"] == source_id)


def frame_grid(video, output):
    from PIL import Image, ImageDraw
    info = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_format", "-show_streams",
        "-of", "json", str(video)], encoding="utf-8"))
    stream = next(s for s in info["streams"] if s["codec_type"] == "video")
    duration = float(info["format"]["duration"])
    if duration <= 0 or int(stream["width"]) <= 0:
        raise ValueError("Invalid video duration or dimensions")
    times = sorted(set(round(min(max(duration - 0.1, 0), t), 3)
                       for t in (0.2, duration * .2, duration * .4,
                                 duration * .6, duration * .8, duration - .3)))
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    grid = Image.new("RGB", (960, 600), "#202020")
    draw = ImageDraw.Draw(grid)
    for n, seconds in enumerate(times):
        frame = output / f"frame_{n + 1:02d}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-threads", "1",
                        "-ss", str(seconds), "-i", str(video), "-frames:v", "1",
                        "-vf", "scale=300:260:force_original_aspect_ratio=decrease",
                        "-filter_threads", "1", str(frame)], check=True,
                       capture_output=True)
        with Image.open(frame) as im:
            x, y = (n % 3) * 320, (n // 3) * 300
            grid.paste(im, (x + (320 - im.width) // 2, y + 24))
            draw.text((x + 10, y + 5), f"{seconds:.3f}s", fill="white")
    grid_path = output / "watermark_review.jpg"
    grid.save(grid_path, quality=93)
    return {"duration": duration, "width": stream["width"],
            "height": stream["height"], "sample_seconds": times,
            "review_grid": str(grid_path.resolve()),
            "review_grid_sha256": digest(grid_path)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--sources", required=True)
    prep.add_argument("--out", required=True)
    reg = sub.add_parser("register")
    reg.add_argument("--out", required=True)
    reg.add_argument("--id", required=True)
    reg.add_argument("--file", required=True)
    reg.add_argument("--evidence", required=True, help="Screenshot of real TikSave result")
    review = sub.add_parser("review")
    review.add_argument("--out", required=True)
    review.add_argument("--id", required=True)
    review.add_argument("--decision", choices=["passed", "failed"], required=True)
    review.add_argument("--note", required=True, help="Actual visual-review observation")
    verify = sub.add_parser("verify")
    verify.add_argument("--out", required=True)
    verify.add_argument("--ids", nargs="+", required=True)
    a = p.parse_args()
    folder = Path(a.out).resolve()
    if a.command == "prepare":
        rows, ids, numbers = [], set(), set()
        for item in read(a.sources):
            url = item["url"].split("?")[0]
            parsed = urlsplit(url)
            match = re.fullmatch(r"/@[^/]+/video/(\d+)", parsed.path.rstrip("/"))
            if parsed.scheme != "https" or parsed.hostname not in ("www.tiktok.com", "tiktok.com") or not match:
                raise ValueError("Use canonical public TikTok video URLs")
            sid, number = match[1], item["source_number"]
            if str(item["id"]) != sid or sid in ids or number in numbers:
                raise ValueError("Duplicate or mismatched fixed source/video ID")
            ids.add(sid)
            numbers.add(number)
            rows.append({"id": sid, "source_number": number, "url": url,
                         "author": item.get("author"), "service_url": SERVICE,
                         "download_method": "TikSave", "status": "pending_browser_download"})
        queue = folder / "queue.json"
        if queue.exists() and read(queue) != rows:
            raise FileExistsError("Existing queue differs; preserve it and use a new output folder")
        write(queue, rows)
        print(json.dumps({"queued": len(rows), "queue": str(queue)}, ensure_ascii=False))
        return
    manifest_path = folder / "manifest.json"
    manifest = read(manifest_path) if manifest_path.exists() else []
    if a.command == "register":
        row = source_row(folder, a.id)
        source, evidence = Path(a.file).resolve(), Path(a.evidence).resolve()
        if not source.is_file() or not evidence.is_file():
            raise FileNotFoundError("Downloaded video and browser-result screenshot are required")
        dest = folder / "videos" / f"{a.id}.mp4"
        if dest.exists() and digest(dest) != digest(source):
            raise FileExistsError("Do not overwrite a registered source; use a new output folder")
        dest.parent.mkdir(parents=True, exist_ok=True)
        if source != dest:
            shutil.copy2(source, dest)
        audit = frame_grid(dest, folder / "reviews" / a.id)
        row.update(audit, video_path=str(dest), sha256=digest(dest),
                   browser_evidence=str(evidence), browser_evidence_sha256=digest(evidence),
                   downloaded_at=stamp(), watermark_review="pending", download_ok=False)
        manifest = [r for r in manifest if r["id"] != a.id] + [row]
        write(manifest_path, manifest)
        print(json.dumps({"id": a.id, "watermark_review": "pending", **audit}, ensure_ascii=False))
        return
    targets = a.ids if a.command == "verify" else [a.id]
    for sid in targets:
        row = next(r for r in manifest if r["id"] == sid)
        if row["download_method"] != "TikSave" or digest(row["video_path"]) != row["sha256"]:
            raise ValueError(f"Source changed or method mismatch: {sid}")
        if digest(row["review_grid"]) != row["review_grid_sha256"] or digest(row["browser_evidence"]) != row["browser_evidence_sha256"]:
            raise ValueError(f"Review evidence changed: {sid}")
        if a.command == "review":
            row.update(watermark_review=a.decision, review_note=a.note,
                       reviewed_at=stamp(), download_ok=a.decision == "passed")
        elif row.get("watermark_review") != "passed" or not row.get("download_ok"):
            raise ValueError(f"Visual watermark review not passed: {sid}")
    if a.command == "review":
        write(manifest_path, manifest)
    print(json.dumps({"ids": targets, "status": a.decision if a.command == "review" else "verified"}))


if __name__ == "__main__":
    main()
