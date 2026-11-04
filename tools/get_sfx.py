"""从 Mixkit 官网下载流程用到的免费音效和配乐到 音效库/（每台电脑自己下载，仓库不转发文件）。

用法: python tools/get_sfx.py        已有的跳过，只补缺的
许可: Mixkit Free License，可免费商用于视频，不可单独转售/再分发素材文件。https://mixkit.co/license/
"""
from pathlib import Path
import sys, urllib.request

SFX = ["2354", "2357", "1491", "1492", "1486", "190", "937", "938", "1430", "1431"]
MUSIC = ["801", "5", "621", "1072"]


def url(kind, n):
    return f"https://assets.mixkit.co/active_storage/sfx/{n}/{n}-preview.mp3" if kind == "sfx" \
        else f"https://assets.mixkit.co/music/{n}/{n}.mp3"


def main():
    lib = Path(__file__).resolve().parent.parent / "音效库"
    lib.mkdir(exist_ok=True)
    jobs = [("sfx", n, lib / f"mixkit_{n}.mp3") for n in SFX] + [("music", n, lib / f"music_{n}.mp3") for n in MUSIC]
    bad = 0
    for kind, n, dst in jobs:
        if dst.exists() and dst.stat().st_size > 1000:
            continue
        try:
            req = urllib.request.Request(url(kind, n), headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                dst.write_bytes(r.read())
            print("下载", dst.name, dst.stat().st_size // 1024, "KB")
        except Exception as e:
            bad += 1
            print("失败", dst.name, e)
    print(f"音效库就绪：{lib}" + (f"（{bad} 个失败，重跑一次即可；缺的音效出片时自动跳过）" if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
