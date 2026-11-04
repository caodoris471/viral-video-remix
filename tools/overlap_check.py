"""新文案与参考爆款口播的文字重合度检查。

指标：
  4字重合率 = 新文案里出现在参考稿中的 4 字连续片段 / 新文案 4 字片段总数（去标点后计算）
  最长相同片段 = 新文案与参考稿最长的连续相同文字
阈值：任一参考 4字重合率 > 30% 或 最长相同片段 ≥ 12 字 → 不通过，需改写。
用法: python overlap_check.py <新文案.txt> <参考_逐句.json> [...]
"""
from pathlib import Path
import json, re, sys

PUNCT = re.compile(r"[\s，。！？、；：,.!?;:“”\"'（）()《》…·\-—]")


def clean(t):
    return PUNCT.sub("", t)


def grams(t, n=4):
    return [t[i:i + n] for i in range(len(t) - n + 1)]


def lcs(a, b):
    best, prev = "", [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                cur[j] = prev[j - 1] + 1
                if cur[j] > len(best):
                    best = a[i - cur[j]:i]
        prev = cur
    return best


new_raw = Path(sys.argv[1]).read_text(encoding="utf-8")
lines = [l.strip() for l in new_raw.splitlines() if l.strip() and not l.startswith("#")]
new = clean("".join(lines))
print(f"新文案：{len(lines)} 句，{len(new)} 字（去标点）")
ok = True
for ref in sys.argv[2:]:
    d = json.loads(Path(ref).read_text(encoding="utf-8"))
    r = clean("".join(s["文本"] for s in d["句"]))
    g = grams(new)
    rs = set(grams(r))
    hit = sum(x in rs for x in g)
    rate = hit / len(g) if g else 0
    m = lcs(new, r)
    bad = rate > 0.30 or len(m) >= 12
    ok &= not bad
    print(f"{'不通过' if bad else '通过'}  {d['文件'][:19]}  4字重合 {rate:.0%}（{hit}/{len(g)}）  最长相同片段 {len(m)} 字：{m}")
print("结论：", "全部通过" if ok else "有不通过项，需改写")
