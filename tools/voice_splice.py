"""口播单句替换：把重录的某几句换进精剪后的主录音，重新拼接并重算逐字时间戳。

每条重录先单独走 voice_prep（对齐该句文稿、压停顿），再替换主录音里的同一句；句间统一留 GAP 秒。
用法: python voice_splice.py <主口播目录(含 口播_精剪.wav, timestamps.json)> <输出目录> <句号>=<录音> [<句号>=<录音> ...]
      句号从 1 开始，按文稿行号
产物: 输出目录/口播_精剪.wav、timestamps.json、口播处理报告.md
"""
from pathlib import Path
import json, subprocess, sys, tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice_prep  # noqa: E402

GAP = 0.28


def cut(src, a, b, dst):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af",
                    f"atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st={max(0, b - a - 0.008):.3f}:d=0.008",
                    "-ac", "1", "-ar", "48000", str(dst)], check=True)


def main(main_dir, outdir, reps):
    main_dir, outdir = Path(main_dir), Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="voice_splice_", dir=outdir))
    ts = json.loads((main_dir / "timestamps.json").read_text(encoding="utf-8"))
    sents = ts["sentences"]
    new = {}
    for k, path in reps.items():
        line = sents[k - 1]["text"]
        sp = tmp / f"line{k}.txt"
        sp.write_text(line + "\n", encoding="utf-8")
        d = tmp / f"line{k}"
        voice_prep.main(path, sp, d, code=ts.get("lang", "zh"))
        t = json.loads((d / "timestamps.json").read_text(encoding="utf-8"))["sentences"][0]
        new[k] = dict(wav=d / "口播_精剪.wav", s=t["start"], e=t["end"], words=t["words"], src=path)

    parts, out_sents, cur = [], [], 0.0
    for i, s in enumerate(sents, 1):
        if i in new:
            n = new[i]
            src, a, b, words = n["wav"], max(0, n["s"] - 0.05), n["e"] + 0.05, n["words"]
        else:
            src, a, b, words = main_dir / "口播_精剪.wav", max(0, s["start"] - 0.05), s["end"] + 0.05, s["words"]
        if i == len(sents):
            b += 0.35
        p = tmp / f"part{i:02d}.wav"
        cut(src, a, b, p)
        parts.append(p)
        off = cur - a
        w2 = [dict(word=w["word"], start=round(w["start"] + off, 3), end=round(w["end"] + off, 3)) for w in words]
        out_sents.append(dict(text=s["text"], start=w2[0]["start"], end=w2[-1]["end"], words=w2, 来源="重录" if i in new else "主录音"))
        cur += b - a
        if i < len(sents):
            g = tmp / f"gap{i:02d}.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=mono", "-t", str(GAP), str(g)],
                           check=True)
            parts.append(g)
            cur += GAP
    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    wav = outdir / "口播_精剪.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c:a", "pcm_s16le", str(wav)], check=True)
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(wav)]))
    (outdir / "timestamps.json").write_text(json.dumps(dict(source=f"{main_dir} + 重录 {sorted(new)}", lang=ts.get("lang", "zh"), duration=round(dur, 3),
                                                            sentences=out_sents), ensure_ascii=False, indent=1), encoding="utf-8")
    chars = sum(len(s["words"]) for s in out_sents)
    rep = [f"# 口播处理报告（单句替换）", "", f"- 主录音：{main_dir / '口播_精剪.wav'}",
           f"- 替换：" + "；".join(f"第{k}句 ← {Path(v['src']).name}" for k, v in sorted(new.items())),
           f"- 时长 {dur:.1f}s，{chars} 字，语速 {chars / dur:.1f} 字/秒；句间统一 {GAP}s；未变速", "",
           "| # | 起 | 止 | 时长 | 来源 | 文本 |", "|---|---|---|---|---|---|"]
    rep += [f"| {i} | {s['start']} | {s['end']} | {s['end'] - s['start']:.1f} | {s['来源']} | {s['text']} |"
            for i, s in enumerate(out_sents, 1)]
    (outdir / "口播处理报告.md").write_text("\n".join(rep) + "\n", encoding="utf-8")
    print("\n".join(rep))


if __name__ == "__main__":
    reps = {int(a.split("=", 1)[0]): a.split("=", 1)[1] for a in sys.argv[3:]}
    main(sys.argv[1], sys.argv[2], reps)
