"""爆款拆解第1步：把参考视频的口播逐句转写成带时间的稿子（本地 faster-whisper，不联网、不收费）。

输出每句的起止时间、字数、语速、句前停顿，供人拆结构（钩子 / 每段讲什么 / 每段几秒 / 节奏 / 结尾引导）。
用法: python transcribe.py <输出目录> <视频1> [视频2 ...] [--lang=zh]（外语对标视频填对应语言，语速单位变成 词/秒）
产物: <输出目录>/<视频名>_逐句.json 和 _逐句.md
"""
from pathlib import Path
import json, sys
import lang as L
from faster_whisper import WhisperModel


def main(out, files, code="zh"):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    model = WhisperModel("small", device="cpu", compute_type="int8")
    for f in map(Path, files):
        segs, info = model.transcribe(str(f), language=L.info(code)["whisper"], vad_filter=True, word_timestamps=True,
                                      initial_prompt="以下是普通话的句子。" if code == "zh" else None)
        rows, prev_end = [], 0.0
        for s in segs:
            text = s.text.strip()
            dur = s.end - s.start
            n = len(L.units(text, code))
            rows.append(dict(起=round(s.start, 2), 止=round(s.end, 2), 文本=text, 字数=n,
                             语速字每秒=round(n / dur, 1) if dur > 0 else None, 句前停顿=round(s.start - prev_end, 2)))
            prev_end = s.end
        total = sum(r["字数"] for r in rows)
        speak = sum(r["止"] - r["起"] for r in rows)
        meta = dict(文件=f.name, 时长=round(info.duration, 1), 句数=len(rows), 总字数=total,
                    平均语速=round(total / speak, 1) if speak else None)
        (out / f"{f.stem}_逐句.json").write_text(json.dumps(dict(meta, 句=rows), ensure_ascii=False, indent=1), encoding="utf-8")
        md = [f"# {f.name} 逐句转写", "", f"时长 {meta['时长']}s · {meta['句数']} 句 · {total} 字 · 平均 {meta['平均语速']} 字/秒", "",
              "| # | 起 | 止 | 停顿 | 字/秒 | 文本 |", "|---|---|---|---|---|---|"]
        md += [f"| {i} | {r['起']} | {r['止']} | {r['句前停顿']} | {r['语速字每秒']} | {r['文本']} |" for i, r in enumerate(rows, 1)]
        (out / f"{f.stem}_逐句.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        print(f"OK {f.name}: {meta}", flush=True)


if __name__ == "__main__":
    code = next((x.split("=", 1)[1] for x in sys.argv if x.startswith("--lang=")), "zh")
    main(sys.argv[1], [x for x in sys.argv[2:] if not x.startswith("--")], code)
