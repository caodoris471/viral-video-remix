"""口播准备（真人录音 / AI 配音通用）：对齐文稿 → 剪掉口误重念 → 压缩长停顿 → 输出精剪音频 + 逐字时间戳。

1 本地 faster-whisper 识别带逐字时间（不联网、不收费）
2 以“文稿”为准逐字对齐：识别错的同音字不影响字幕，字幕和关键词时间用文稿的字
3 录音里多出来、文稿里没有的连续片段（口误、重念）记为剪除
4 句内停顿 > 句内上限 压到 句内保留；句间停顿 > 句间上限 压到 句间保留；不变速
用法: python voice_prep.py <录音> <文稿.txt> <输出目录> [--no-cut] [--lang=zh]（语言见 lang.py；英语等按词对齐）
产物: 口播_精剪.wav、timestamps.json（流程格式：sentences[text,start,end,words]）、口播处理报告.md
"""
from pathlib import Path
import difflib, json, re, subprocess, sys
import lang as L

IN_MAX, IN_KEEP = 0.25, 0.18      # 句内停顿：超过 0.25s 压到 0.18s
BT_MAX, BT_KEEP = 0.35, 0.28      # 句间停顿：超过 0.35s 压到 0.28s
HEAD, TAIL = 0.15, 0.40
PUNCT = re.compile(r"[\s，。！？、；：,.!?;:“”\"'（）()《》…·\-—]")


def asr_chars(audio, code="zh"):
    from faster_whisper import WhisperModel
    li = L.info(code)
    m = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = m.transcribe(str(audio), language=li["whisper"], word_timestamps=True, vad_filter=False,
                           initial_prompt="以下是普通话的句子。" if code == "zh" else None)
    out = []
    for s in segs:
        for w in s.words or []:
            if li["spaced"]:
                out += [dict(ch=u, s=w.start, e=w.end) for u, _ in L.units(w.word, code)]
                continue
            t = PUNCT.sub("", w.word)
            if not t:
                continue
            step = (w.end - w.start) / len(t)
            out += [dict(ch=c, s=w.start + i * step, e=w.start + (i + 1) * step) for i, c in enumerate(t)]
    return out


def main(audio, script, outdir, do_cut=True, code="zh"):
    audio, outdir = Path(audio), Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    lines = [l.strip() for l in Path(script).read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    sc = [(u, li) for li, l in enumerate(lines) for u, _ in L.units(l, code)]
    A = asr_chars(audio, code)
    a_str, s_str = [x["ch"] for x in A], [c for c, _ in sc]
    t = [None] * len(sc)            # 每个文稿字的 (起, 止)
    extras = []                     # 录音里多出来的片段
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a_str, s_str, autojunk=False).get_opcodes():
        if op == "equal" or (op == "replace" and i2 - i1 == j2 - j1):
            for k in range(j2 - j1):
                t[j1 + k] = (A[i1 + k]["s"], A[i1 + k]["e"])
        elif op == "replace":
            s0, e0 = A[i1]["s"], A[i2 - 1]["e"]
            n = j2 - j1
            for k in range(n):
                t[j1 + k] = (s0 + (e0 - s0) * k / n, s0 + (e0 - s0) * (k + 1) / n)
        elif op == "delete":
            span = (A[i1]["s"], A[i2 - 1]["e"])
            if span[1] - span[0] >= 0.25 and i2 - i1 >= 2:
                extras.append(dict(文本=L.join(a_str[i1:i2], code), 起=round(span[0], 2), 止=round(span[1], 2)))
    for k in range(len(t)):         # 识别漏掉的字：用前后字插值
        if t[k] is None:
            prev = next((t[j] for j in range(k - 1, -1, -1) if t[j]), (0, 0))
            nxt = next((t[j] for j in range(k + 1, len(t)) if t[j]), prev)
            t[k] = (prev[1], max(prev[1], nxt[0]))

    # 保留区间：从文稿字的时间线出发，删掉口误片段，压缩停顿
    cuts = [(x["起"] - 0.02, x["止"] + 0.02) for x in extras] if do_cut else []
    marks = sorted([(t[k][0], t[k][1], sc[k][1]) for k in range(len(sc))])
    keep, sil_saved = [], 0.0
    start = max(0.0, marks[0][0] - HEAD)
    for (s0, e0, l0), (s1, e1, l1) in zip(marks, marks[1:]):
        gap = s1 - e0
        lim, kp = (BT_MAX, BT_KEEP) if l1 != l0 else (IN_MAX, IN_KEEP)
        if gap > lim:
            keep.append((start, e0 + kp / 2))
            start = s1 - kp / 2
            sil_saved += gap - kp
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(audio)]))
    keep.append((start, min(dur, marks[-1][1] + TAIL)))
    for c0, c1 in cuts:             # 再从保留区间里挖掉口误
        nk = []
        for a, b in keep:
            if c1 <= a or c0 >= b:
                nk.append((a, b))
            else:
                if c0 > a:
                    nk.append((a, c0))
                if c1 < b:
                    nk.append((c1, b))
        keep = nk
    keep = [(a, b) for a, b in keep if b - a > 0.03]

    def remap(x):
        acc = 0.0
        for a, b in keep:
            if x < a:
                return acc
            if x <= b:
                return acc + x - a
            acc += b - a
        return acc

    chains = [f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st={b - a - 0.008:.3f}:d=0.008[k{i}]"
              for i, (a, b) in enumerate(keep)]
    g = ";".join(chains) + ";" + "".join(f"[k{i}]" for i in range(len(keep))) + f"concat=n={len(keep)}:v=0:a=1,aresample=48000[out]"
    (outdir / "_voice_filter.txt").write_text(g, encoding="utf-8")
    wav = outdir / "口播_精剪.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(audio), "-/filter_complex", str(outdir / "_voice_filter.txt"),
                    "-map", "[out]", "-ac", "1", str(wav)], check=True)
    new_dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(wav)]))

    sents = []
    for li, l in enumerate(lines):
        ks = [k for k in range(len(sc)) if sc[k][1] == li]
        words = [dict(word=sc[k][0], start=round(remap(t[k][0]), 3), end=round(remap(t[k][1]), 3)) for k in ks]
        sents.append(dict(text=l, start=words[0]["start"], end=words[-1]["end"], words=words))
    (outdir / "timestamps.json").write_text(json.dumps(dict(source=str(audio), lang=code, duration=round(new_dur, 3), sentences=sents),
                                                       ensure_ascii=False, indent=1), encoding="utf-8")
    spoken = len(sc)
    rep = [f"# 口播处理报告：{audio.name}", "",
           f"- 原始 {dur:.1f}s → 精剪 {new_dur:.1f}s（压缩停顿省 {sil_saved:.1f}s，剪口误 {len(extras) if do_cut else 0} 处）；未变速",
           f"- 文稿 {len(lines)} 句 {spoken} {"词" if L.info(code)["spaced"] else "字"}，精剪后语速 {spoken / new_dur:.1f}/秒（中文爆款参考 5–6 字/秒，英语约 2.5–3 词/秒）",
           "", "## 剪掉的口误 / 文稿外内容（请听一下确认）", ""]
    rep += [f"- {x['起']}–{x['止']}s：“{x['文本']}”" for x in extras] or ["- 无"]
    rep += ["", "## 逐句时间（精剪后）", "", "| # | 起 | 止 | 文本 |", "|---|---|---|---|"]
    rep += [f"| {i} | {s['start']} | {s['end']} | {s['text']} |" for i, s in enumerate(sents, 1)]
    (outdir / "口播处理报告.md").write_text("\n".join(rep) + "\n", encoding="utf-8")
    print("\n".join(rep[:6] + rep[6:6 + len(extras) + 1]))


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    code = next((x.split("=", 1)[1] for x in sys.argv if x.startswith("--lang=")), "zh")
    main(a[0], a[1], a[2], do_cut="--no-cut" not in sys.argv, code=code)
