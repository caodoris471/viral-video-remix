"""各步骤共用：读配置、句子时间、段落起止、关键词开口时间。"""
from pathlib import Path
import json
import lang as L


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def save(p, data):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def lang_of(beats):
    return load(beats["时间戳"]).get("lang", "zh")


def sentences(beats):
    ss = load(beats["时间戳"])["sentences"]
    if beats.get("首句起点") is not None:
        ss[0] = dict(ss[0], start=beats["首句起点"])
    return ss


def beat_onset(b, ss):
    """段第一个字的开口时间：“起字”= 该句第几个字（0=句首），只应填在句内逗号/顿号停顿后的字上。"""
    s = ss[b["句"][0]]
    k = b.get("起字", 0)
    return s["words"][k]["start"] if k else s["start"]


def beat_times(beats, cfg):
    """段起点 = 该段第一个字开口前 N 帧（第一段从 0 开始）；段终点 = 下一段起点（最后一段到总时长）。
    切点因此只落在句与句之间、或句内逗号停顿处，不会切在词中间。"""
    ss = sentences(beats)
    lead = cfg["规则"]["切点提前帧"] / cfg["画布"]["帧率"]
    starts = [0.0] + [max(0.0, beat_onset(b, ss) - lead) for b in beats["段"][1:]]
    ends = starts[1:] + [beats["总时长"]]
    return [(round(a, 3), round(e, 3)) for a, e in zip(starts, ends)]


def word_onset(sents, word, window=None, code="zh"):
    """在给定句子里找词，返回第一个字的开口时间；找不到返回 None。
    window=(起, 止)：只认开口时间落在这段时间里的词（一句拆成两段时，避免抢到另一段的词）。
    英语等按词计时的语言：大小写、标点不敏感，按整词连空格匹配。"""
    spaced = L.info(code)["spaced"]
    if spaced:
        word = L.join([u for u, _ in L.units(word, code)], code)
    for s in sents:
        chars = []
        for n, w in enumerate(s.get("words", [])):
            text = w.get("word", w.get("text", ""))
            if spaced and n:
                chars.append((" ", w["start"]))
            chars += [(ch, w["start"]) for ch in text]
        joined = "".join(c for c, _ in chars)
        i = joined.find(word)
        while i >= 0:
            t = chars[i][1]
            if window is None or window[0] - 0.1 <= t < window[1]:
                return t
            i = joined.find(word, i + 1)
    return None


def clip_geom(crop, sw, sh, W, H, mul=1.0):
    """裁切窗（归一化 x0,y0,w,h）→ 剪映 ClipSettings：缩放和半画布单位位移（y 向上为正）。
    剪映把素材按“完整放进画布”的比例显示，再乘以缩放。"""
    s0 = min(W / sw, H / sh)
    k = W / (crop["w"] * sw * s0) * mul
    cx, cy = crop["x0"] + crop["w"] / 2, crop["y0"] + crop["h"] / 2
    tx = -(cx - 0.5) * sw * s0 * k / (W / 2)
    ty = (cy - 0.5) * sh * s0 * k / (H / 2)
    return k, tx, ty
