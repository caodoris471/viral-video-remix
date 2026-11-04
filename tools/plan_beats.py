"""分镜第0步：按口播时间自动建议分段。只在“句与句之间”或“句内逗号/顿号停顿处”切，每段 最短–最长 秒。

用法: python plan_beats.py <项目目录> <timestamps.json>
输出每段：句号、起字（句内第几个字开始，0=句首）、时长、文本。拿去填分镜的“句”和“起字”，再补“必需/优先/关键词”。
"""
from pathlib import Path
import json, re, sys
from common import load
import lang as L

CLAUSE = re.compile(r"[，、；：,;:]")
PUNCT = re.compile(r"[\s，。！？、；：,.!?;:“”\"'（）()《》…·\-—]")


def clauses(sents, code="zh"):
    """把每句按逗号/顿号拆成小句：(句号, 起字, 止字, 起时, 止时, 文本)。英语等“起字”= 句内第几个词。"""
    out = []
    for si, s in enumerate(sents):
        w, us = s["words"], L.units(s["text"], code)
        cut = [k for k, (_, brk) in enumerate(us) if brk] + [len(us)]
        for a, b in zip(cut, cut[1:]):
            if b > a:
                out.append((si, a, b, w[a]["start"], w[b - 1]["end"], L.join([u for u, _ in us[a:b]], code)))
    return out


def plan(sents, mn, mx, code="zh"):
    us = clauses(sents, code)
    beats, cur = [], []
    for i, u in enumerate(us):
        cur.append(u)
        d = u[4] - cur[0][3]
        nxt = us[i + 1] if i + 1 < len(us) else None
        if nxt is None:
            beats.append(cur)
            break
        nd = nxt[4] - cur[0][3]
        if (d >= mn and (nxt[0] != u[0] or nd > mx)) or d >= mx:
            beats.append(cur)
            cur = []
    if len(beats) > 1 and beats[-1][-1][4] - beats[-1][0][3] < mn:
        tail = beats.pop()
        beats[-1] = beats[-1] + tail
    return beats


if __name__ == "__main__":
    cfg = load(Path(sys.argv[1]) / "config.json")
    ts = load(sys.argv[2])
    sents, code = ts["sentences"], ts.get("lang", "zh")
    R = cfg["规则"]
    mn = float(sys.argv[3]) if len(sys.argv) > 3 else R["最短镜头秒"]   # 可选：python plan_beats.py 项目 时间戳 最短 最长
    mx = float(sys.argv[4]) if len(sys.argv) > 4 else R["最长镜头秒"]
    for n, b in enumerate(plan(sents, mn, mx, code), 1):
        d = b[-1][4] - b[0][3]
        flag = "" if mn <= d <= mx else "  <-- 超出范围，单个小句太长/太短"
        print(f"段{n:2d} 句{sorted({u[0] for u in b})} 起字{b[0][1]:2d} {b[0][3]:6.2f}-{b[-1][4]:6.2f} {d:4.1f}s  "
              f"{'，'.join(u[5] for u in b)}{flag}")
