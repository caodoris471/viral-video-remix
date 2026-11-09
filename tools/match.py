"""第3步 配镜头：按分镜每段的“必需标签”给镜头窗打分并分配，产出 EDL。

硬规则：段长 >= 最短镜头秒；镜头窗必须含全部“必需”标签、不含“排除”标签、时长够；
一个窗只用一次，同一原镜头拆出的相邻窗不给相邻段；静态窗（运动量 < 动态阈值）全片不超过上限。
产品类只选已复核且完整匹配必需标签的窗；缺合格窗就报缺镜头。其他项目可按原流程降级匹配。

用法: python match.py <项目目录> <分镜文件名>
"""
from pathlib import Path
import sys
from common import load, save, sentences, beat_times, word_onset, lang_of, tagged_pool, full_motion
from caption_layout import fit_captions
import lang as L

CUE_FOR_TRANSITION = {"闪白": "shutter", "模糊": "whoosh", "叠化": "chime"}


def main(proj, beats_name, preview=False):
    """preview=True（--预演）：缺镜头的段放占位卡继续出片，成片质检会标为不通过。"""
    proj = Path(proj)
    cfg, R = load(proj / "config.json"), load(proj / "config.json")["规则"]
    beats = load(proj / beats_name)
    if full_motion(cfg, beats):
        R = dict(R, 静态镜头上限=0)
        if any("用图" in b for b in beats["段"]):
            sys.exit("全动态模式不能使用整屏图片；产品PNG请放在独立角标轨")
    cands = load(proj / "work/candidates.json")["窗"]
    tags = load(proj / "work/tags.json")
    pool = tagged_pool(cands, tags, cfg)
    # 同一原镜头拆出的窗归为一组（同源、首尾相接）
    pool.sort(key=lambda c: (c["源文件"], c["入"]))
    for i, c in enumerate(pool):
        p = pool[i - 1] if i else None
        same = p and p["源文件"] == c["源文件"] and c["入"] - p["出"] < 0.25
        c["组"] = p["组"] if same else f"{c['源文件']}@{c['入']}"

    times = beat_times(beats, cfg)
    ss = sentences(beats)
    code = lang_of(beats)
    problems = []
    for i, (b, (a, e)) in enumerate(zip(beats["段"], times)):
        b["_起止"] = (a, e)
        if e - a < R["最短镜头秒"] - 1e-6:
            problems.append(f"段{i + 1} 只有 {e - a:.2f}s，短于最短镜头 {R['最短镜头秒']}s：请在分镜里和相邻句合并")
        if e - a > R["最长镜头秒"] + 1e-6 and "用图" not in b:
            problems.append(f"段{i + 1} 有 {e - a:.2f}s，超过最长镜头 {R['最长镜头秒']}s：请在句与句之间拆开")
    if problems:
        sys.exit("分镜不合规：\n" + "\n".join(problems))

    def eligible(b, need):
        d = b["_起止"][1] - b["_起止"][0]
        return [c for c in pool if set(need) <= set(c["标签"]) and c["时长"] >= d]

    def score(c, b):
        pref = len(set(b.get("优先", [])) & set(c["标签"]))
        return pref * 3 + min(c["运动量"], 10) * 0.6 + min(c["裁切像素宽"], 1080) / 540

    video_idx = [i for i, b in enumerate(beats["段"]) if "用图" not in b]
    # 先排“只有静态窗可选”的段（如墙面特写），静态名额优先给它们；再按可选窗少的先排
    def n_dyn(i):
        return sum(c["运动量"] >= R["动态阈值"] for c in eligible(beats["段"][i], beats["段"][i]["必需"]))
    order = sorted(video_idx, key=lambda i: (n_dyn(i) > 0, len(eligible(beats["段"][i], beats["段"][i]["必需"]))))
    used, groups_at, statics, picks, notes, missing = set(), {}, 0, {}, [], []
    # 分镜里写了“指定窗”的段先放（自动分配是贪心的，几段抢同一类窗时可能排不开）；规则照样检查
    by_id = {c["id"]: c for c in pool}
    for i in video_idx:
        b = beats["段"][i]
        if "指定窗" not in b:
            continue
        c = by_id.get(b["指定窗"])
        d = b["_起止"][1] - b["_起止"][0]
        err = ("不在可用窗里（不存在、不可用或带排除标签）" if c is None else
               f"缺必需标签 {sorted(set(b['必需']) - set(c['标签']))}" if not set(b["必需"]) <= set(c["标签"]) else
               f"只有 {c['时长']}s，段长 {d:.2f}s" if c["时长"] < d else
               "已被别的段指定" if c["id"] in used else "")
        if err:
            sys.exit(f"段{i + 1} 指定窗 {b['指定窗']} 不合规：{err}")
        used.add(c["id"])
        groups_at[i] = c["组"]
        statics += c["运动量"] < R["动态阈值"]
        picks[i] = c
    if statics > R["静态镜头上限"]:
        sys.exit(f"指定窗里静态镜头 {statics} 个，超过上限 {R['静态镜头上限']}")
    for i in [i for i in order if i not in picks]:
        b = beats["段"][i]
        levels = [("完全匹配", b["必需"])]
        if cfg.get("任务类型") != "产品类":
            levels.append(("降级：只保留第一个必需", b["必需"][:1]))
        chosen = None
        for label, need in levels:
            # 同一原镜头（连续拍的一条）全片只用一次：同一面墙拆出的两个窗不再先后出现
            opts = [c for c in eligible(b, need) if c["id"] not in used and c["组"] not in set(groups_at.values())]
            dyn = [c for c in opts if c["运动量"] >= R["动态阈值"]]
            if not dyn and statics >= R["静态镜头上限"]:
                continue
            opts = dyn or opts
            if opts:
                # 同一要点内优先用同一条原片的镜头（对标视频讲一项就连着用同一家店的几个镜头）
                same = {picks[j]["源文件"] for j in picks if beats["段"][j].get("要点") and beats["段"][j].get("要点") == b.get("要点")}
                chosen = max(opts, key=lambda c: score(c, b) + (4 if c["源文件"] in same else 0))
                if label != "完全匹配":
                    notes.append(f"段{i + 1}：{label}（{need}）")
                break
        if chosen is None:
            msg = (f"缺镜头：段{i + 1}（{''.join(ss[k]['text'] for k in b['句'])}）需要 {b['必需']}，素材库里没有合格的窗。")
            if not preview:
                sys.exit(msg + "\n处理：补素材 / 给已有窗补标签 / 改这句的必需画面。不要拿不相关的镜头凑。")
            missing.append(dict(段=i + 1, 必需=b["必需"]))   # 预演：放占位卡，不拿无关镜头凑
            continue
        used.add(chosen["id"])
        groups_at[i] = chosen["组"]
        if chosen["运动量"] < R["动态阈值"]:
            statics += 1
        picks[i] = chosen

    shots, image = [], None
    for i, b in enumerate(beats["段"]):
        a, e = b["_起止"]
        if "用图" in b:
            image = dict(文件=b["用图"], 起=a, 止=e, 平移=b.get("平移", 0.9))
            continue
        if i not in picks:
            shots.append(dict(段=i + 1, 起=a, 止=e, 占位=True, 必需=b["必需"], 出转场=b.get("出转场"),
                              文本="缺镜头 · 需要：" + "、".join(b["必需"])))
            continue
        c = picks[i]
        slack = c["时长"] - (e - a)
        shots.append(dict(段=i + 1, 起=a, 止=e, 窗=c["id"], 源文件=c["源文件"], 源宽=c["源宽"], 源高=c["源高"],
                          源入点=round(c["入"] + min(slack / 2, 0.5), 3), 窗出=c["出"], 裁切=c["裁切"],
                          宽裁切=c.get("宽裁切"),
                          推近=R["静态推近"] if c["运动量"] < R["动态阈值"] else 1.0, 出转场=b.get("出转场"),
                          标签=c["标签"], 必需=b["必需"], 运动量=c["运动量"], 像素宽=c["裁切像素宽"]))

    keywords, sfx = [], []
    list_end = image["起"] if image else beats["总时长"]
    for i, b in enumerate(beats["段"]):
        a, e = b["_起止"]
        sents = [ss[k] for k in b["句"]]
        big = [k for k in b.get("关键词", []) if k.get("样式", "大字") == "大字"]
        for k in b.get("关键词", []):
            t = word_onset(sents, k["词"], window=(a, e), code=code)
            if t is None:
                sys.exit(f"段{i + 1} 的关键词“{k['词']}”在口播时间戳里找不到，检查用字是否和录音一致")
            k["_t"] = t
        for j, k in enumerate(big):
            end = big[j + 1]["_t"] if j + 1 < len(big) else e
            keywords.append(dict(文本=k.get("显示", k["词"]), 起=round(k["_t"], 3), 止=round(end, 3), 槽=None))
        for k in b.get("关键词", []):
            if k.get("样式") == "清单":
                keywords.append(dict(文本=k["显示"], 起=round(k["_t"], 3), 止=round(list_end, 3), 槽=k["槽"]))
            kind = k.get("音效")   # 只在分镜里明确写了音效的关键词上放（对标视频音效很少）
            if kind:
                sfx.append(dict(类型=kind, 时间=round(k["_t"] - cfg["音效"][kind]["提前"], 3), 原因=f"关键词 {k['词']}"))
        if b.get("出转场"):
            kind = CUE_FOR_TRANSITION[b["出转场"]]
            sfx.append(dict(类型=kind, 时间=round(e - cfg["音效"][kind]["提前"], 3), 原因=f"{b['出转场']}转场"))
    captions = []
    for s in ss:   # 句字幕按逗号/顿号拆成短行（每行 ≤ 字幕每行字数），时间用该行第一个字的开口
        if L.info(code)["spaced"]:   # 按词计时：字幕保留原文大小写和标点，按词切行
            toks = s["text"].split()
            chunks, k0, n, buf = [], 0, 0, []
            for k, tok in enumerate(toks):
                buf.append(tok)
                n += bool(L.PUNCT.sub("", tok))
                if tok[-1] in L.BREAK or k == len(toks) - 1:
                    chunks.append((k0, " ".join(buf)))
                    k0, buf = n, []
            limit = R.get("字幕每行字符", 26)
        else:
            chunks, k, buf, k0 = [], 0, "", 0
            for ch in s["text"]:
                if ch in "，、；：,;:。！？.!?":
                    if buf:
                        chunks.append((k0, buf))
                    buf, k0 = "", k
                elif ch.strip():
                    buf += ch
                    k += 1
            if buf:
                chunks.append((k0, buf))
            limit = R.get("字幕每行字数", 11)
        merged = []
        for c in chunks:
            if merged and len(merged[-1][1]) + len(c[1]) + 1 <= limit:
                merged[-1] = (merged[-1][0], merged[-1][1] + " " + c[1])
            else:
                merged.append(c)
        w = s["words"]
        for j, (kk, text) in enumerate(merged):
            a0 = w[kk]["start"] if kk < len(w) else s["start"]
            e0 = w[merged[j + 1][0]]["start"] if j + 1 < len(merged) else s["end"]
            captions.append(dict(文本=text, 起=round(a0, 3), 止=round(e0, 3)))
    captions = fit_captions(captions, load(beats["时间戳"]), code, cfg)
    edl = dict(语言=code, 爆款结构=beats.get("爆款结构"), 对标链接=beats.get("对标链接"), 版本=beats["版本"], 草稿名=beats["草稿名"], 总时长=beats["总时长"], 口播=beats["口播"], 时间戳=beats["时间戳"],
               镜头=shots, 结尾图=image, 字幕=captions, 关键词=keywords, 音效=sorted(sfx, key=lambda s: s["时间"]),
               配乐=cfg["配乐"], 降级=notes, 缺镜头=missing, 预演=preview)
    for key in ("目标时长秒", "时长容差秒", "产品角标", "画面模式", "主结构对标", "结构主题", "结构改编"):
        value = beats.get(key, cfg.get(key))
        if value is not None or key in beats:
            edl[key] = value
    out = proj / "work" / f"EDL_{beats['版本']}.json"
    save(out, edl)
    for s in shots:
        if s.get("占位"):
            print(f"段{s['段']} {s['起']:5.2f}-{s['止']:5.2f} ({s['止'] - s['起']:.2f}s) 【占位】{s['文本']}")
            continue
        print(f"段{s['段']} {s['起']:5.2f}-{s['止']:5.2f} ({s['止'] - s['起']:.2f}s) 窗{s['窗']} 运动{s['运动量']:4.1f} "
              f"{s['像素宽']}px 推近{s['推近']} 必需{s['必需']} 有{s['标签']}")
    if image:
        print(f"段  结尾图 {image['起']:.2f}-{image['止']:.2f}")
    print("降级:", notes or "无", "| 缺镜头:", [m["段"] for m in missing] or "无", "| 输出", out)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args[0], args[1], preview="--预演" in sys.argv)
