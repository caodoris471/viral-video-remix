"""Measure subtitles with the rendered font; split wide word-based lines on timestamps."""
from functools import lru_cache
import math

from PIL import ImageFont
import lang as L


DEFAULT_SIZE = 60


@lru_cache(maxsize=64)
def caption_font(code, size=DEFAULT_SIZE):
    return ImageFont.truetype(L.info(code)["font"], size)


def safe_width(cfg):
    ratio = cfg["规则"].get("字幕安全宽度比例", 0.86)
    if not isinstance(ratio, (int, float)) or not math.isfinite(ratio) or not 0 < ratio <= 1:
        raise ValueError("字幕安全宽度比例必须在 0–1 之间")
    return cfg["画布"]["宽"] * ratio


def width(caption, code):
    size = caption.get("字号", DEFAULT_SIZE)
    if not isinstance(size, int) or size < 24:
        raise ValueError("字幕字号必须是至少24的整数；请先缩短文案")
    return max((caption_font(code, size).getlength(line) for line in caption["文本"].splitlines()), default=0)


def fit_single(caption, code, limit):
    """Keep an indivisible token or a shaped-language line intact; scale both exports."""
    fitted = dict(caption)
    size = fitted.get("字号", DEFAULT_SIZE)
    while size >= 24:
        fitted["字号"] = size
        if width(fitted, code) <= limit:
            return fitted
        size -= 1
    raise ValueError(f"字幕过长，缩小后仍不可读，请缩短：{caption['文本']}")


def fit_captions(captions, timestamp_data, code, cfg):
    limit = safe_width(cfg)
    timeline = [w for s in timestamp_data.get("sentences", []) for w in s.get("words", [])]
    result = []
    for caption in captions:
        if width(caption, code) <= limit:
            result.append(dict(caption))
            continue
        if not L.info(code)["spaced"] or "\n" in caption["文本"]:
            result.append(fit_single(caption, code, limit))
            continue
        # Attach punctuation-only tokens to the preceding spoken token. They do
        # not consume a word timestamp (the same rule as lang.units).
        parts, prefix = [], ""
        for token in caption["文本"].split():
            if L.units(token, code):
                parts.append(prefix + token)
                prefix = ""
            elif parts:
                parts[-1] += " " + token
            else:
                prefix += token + " "
        if not parts or not timeline:
            raise ValueError("长字幕缺逐词时间戳，不能可靠分屏")
        anchor = min(range(len(timeline)), key=lambda i: abs(timeline[i]["start"] - caption["起"]))
        words = timeline[anchor:anchor + len(parts)]
        actual = [L.units(w.get("word", w.get("text", "")), code) for w in words]
        expected = [L.units(p, code) for p in parts]
        # A caption's first token is a phrase onset even when the matching word
        # is in the middle of the sentence; compare token text, not break flags.
        normalize = lambda rows: [[u for u, _ in row] for row in rows]
        if abs(timeline[anchor]["start"] - caption["起"]) > 0.05 or normalize(actual) != normalize(expected):
            raise ValueError(f"字幕与逐词时间戳不匹配，请重做该行：{caption['文本']}")
        groups, current = [], []
        font = caption_font(code, caption.get("字号", DEFAULT_SIZE))
        for i, part in enumerate(parts):
            candidate = " ".join(parts[j] for j in current + [i])
            if current and font.getlength(candidate) > limit:
                groups.append(current)
                current = []
            current.append(i)
        if current:
            groups.append(current)
        for i, group in enumerate(groups):
            item = dict(caption, 文本=" ".join(parts[j] for j in group),
                        起=caption["起"] if i == 0 else words[group[0]]["start"],
                        止=words[groups[i + 1][0]]["start"] if i + 1 < len(groups) else caption["止"])
            if item["止"] <= item["起"]:
                raise ValueError("字幕分屏后时间无效，请检查逐词时间戳")
            result.append(item if width(item, code) <= limit else fit_single(item, code, limit))
    return result
