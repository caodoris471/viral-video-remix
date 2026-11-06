"""第5步 自检：逐段对照图 + 自动检查。不过关的项要先修，再交给人看。

自动检查：
  1 镜头时长 >= 最短镜头秒
  2 每个切点都在某行字幕开口前 0–0.15s（切在句与句之间或句内逗号停顿处，不在词中间）
  3 镜头窗标签包含该段全部“必需”标签（画面里有台词说的东西）
  4 同一镜头窗不重复使用；静态镜头不超过上限
  5 取用的源片段没有越过镜头窗终点（不会闪进下一个镜头）
  6 成片时长、帧数与 EDL 一致。约定时长给提示，明确容差才作为验收条件
用法: python qa.py <项目目录> <版本名，如 真人版>
"""
from pathlib import Path
import json, math, subprocess, sys
from common import load, PRODUCT_REVIEW_TAG
import lang as L

FONT = "C\\:/Windows/Fonts/msyhbd.ttc"


def main(proj, version):
    proj = Path(proj)
    cfg = load(proj / "config.json")
    R, FPS = cfg["规则"], cfg["画布"]["帧率"]
    out = proj / "output" / version
    edl = load(out / "编辑决定表.json")
    mp4 = out / f"{edl['草稿名']}_预览.mp4"
    shots = edl["镜头"]
    # 合法切点 = 每句第一个字、以及句内每个逗号/顿号后第一个字的开口时间（直接从口播时间戳算，不依赖字幕怎么分行）
    starts = []
    tsd = load(edl["时间戳"]) if edl.get("时间戳") else {}
    for snt in tsd.get("sentences", []):
        for k, (_, brk) in enumerate(L.units(snt["text"], tsd.get("lang", "zh"))):
            if brk and k < len(snt["words"]):
                starts.append(snt["words"][k]["start"])
    starts = starts or [c["起"] for c in edl["字幕"]]
    fails = [f"段{s['段']} 缺镜头（预演占位卡）：需要 {s['必需']}" for s in shots if s.get("占位")]
    for s in shots:
        if s.get("占位"):
            continue
        d = s["止"] - s["起"]
        if d < R["最短镜头秒"] - 1e-6:
            fails.append(f"段{s['段']} 时长 {d:.2f}s < {R['最短镜头秒']}s")
        labels = set(s["标签"])
        if cfg.get("任务类型") == "产品类" and PRODUCT_REVIEW_TAG not in labels:
            fails.append(f"段{s['段']} 缺产品入剪复核")
        miss = set(s["必需"]) - labels
        if miss:
            fails.append(f"段{s['段']} 画面缺 {sorted(miss)}（降级匹配，需人工确认）")
        if s["源入点"] + d > s["窗出"] + 1e-3:
            fails.append(f"段{s['段']} 取到镜头窗以外 {s['源入点'] + d - s['窗出']:.2f}s")
    cut_shots = shots if edl.get("结尾图") else shots[:-1]
    cuts = [s["止"] for s in cut_shots]
    for t in cuts:
        if not any(0 <= st - t <= 0.15 for st in starts):
            fails.append(f"切点 {t:.2f}s 不在句子开头前，可能切在句中")
    ids = [s["窗"] for s in shots if not s.get("占位")]
    if len(ids) != len(set(ids)):
        fails.append(f"镜头窗重复使用：{ids}")
    statics = sum(s.get("推近", 1.0) != 1.0 for s in shots)
    if statics > R["静态镜头上限"]:
        fails.append(f"静态镜头 {statics} 个 > 上限 {R['静态镜头上限']}")
    probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
                                                "-show_entries", "stream=nb_read_frames:format=duration", "-of", "json", str(mp4)]))
    frames, dur = int(probe["streams"][0]["nb_read_frames"]), float(probe["format"]["duration"])
    if abs(dur - edl["总时长"]) > 0.05 or abs(frames - round(edl["总时长"] * FPS)) > 1:
        fails.append(f"成片 {dur:.2f}s/{frames}帧，应为 {edl['总时长']}s/{round(edl['总时长'] * FPS)}帧")

    target = edl.get("目标时长秒", cfg.get("目标时长秒"))
    if target is not None:
        tolerance = edl.get("时长容差秒", cfg.get("时长容差秒"))
        if not isinstance(target, (int, float)) or not math.isfinite(target) or target <= 0:
            fails.append("目标时长秒必须填写正数")
        elif tolerance is None:
            if abs(dur - target) > target * 0.10:
                print(f"时长提醒：成片实测 {dur:.2f}s，参考目标约 {target:g}s，建议复看内容和节奏")
        elif not isinstance(tolerance, (int, float)) or not math.isfinite(tolerance) or tolerance < 0:
            fails.append("时长容差秒必须填写非负数")
        elif abs(dur - target) > tolerance + 1 / FPS:
            fails.append(f"成片实测 {dur:.2f}s，目标 {target:g}s ±{tolerance:g}s，超出容差")

    # 逐段对照图：段中点画面 + 段号/时长/必需/实际标签 + 该段字幕
    tiles = []
    # 冒号用全角：drawtext 会把半角冒号当成参数分隔符
    beats = [(s["段"], s["起"], s["止"], f"需：{'/'.join(s['必需'])}",
              "【缺镜头】" if s.get("占位") else f"有：{'/'.join(s['标签'])}",
              "" if s.get("占位") else f"{s['窗']} 动{s['运动量']}") for s in shots]
    if edl["结尾图"]:
        im = edl["结尾图"]
        beats.append(("图", im["起"], im["止"], "用户原图", "", ""))
    for n, a, b, need, have, info in beats:
        cap = " ".join(c["文本"] for c in edl["字幕"] if c["起"] < b and c["止"] > a)
        tile = out / f"_qa_{n}.png"
        lines = [f"段{n} {a:.2f}-{b:.2f} ({b - a:.1f}s)", need, have, info, cap[:14], cap[14:28]]
        dt = ",".join(f"drawtext=fontfile='{FONT}':text='{t}':x=6:y=h-150+{i * 24}:fontsize=18:fontcolor=white"
                      for i, t in enumerate(lines) if t)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str((a + b) / 2), "-i", str(mp4), "-frames:v", "1", "-vf",
                        f"scale=240:427,pad=240:577:0:0:black,{dt}", str(tile)], check=True)
        tiles.append(tile)
    tiles += [tiles[-1]] * (-len(tiles) % 6)   # 每行 6 张，不够的用最后一张补齐
    args = sum((["-i", str(t)] for t in tiles), [])
    sheet = out / "检查_逐段对照.png"
    rows = len(tiles) // 6
    parts = [f"{''.join(f'[{r * 6 + k}:v]' for k in range(6))}hstack=inputs=6[r{r}]" for r in range(rows)]
    g = ";".join(parts) + ";" + "".join(f"[r{r}]" for r in range(rows)) + f"vstack=inputs={rows}" if rows > 1 \
        else parts[0].replace("[r0]", "")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", g, str(sheet)], check=True)
    tiles = list(dict.fromkeys(tiles))
    for t in tiles:
        t.unlink()
    loud = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(mp4), "-af", "ebur128", "-f", "null", "-"],
                          capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    lufs = [l.split()[-2] for l in loud.splitlines() if l.strip().startswith("I:")][-1]
    lens = [round(s["止"] - s["起"], 2) for s in shots]
    print(f"{version}: {dur:.2f}s {frames}帧 {lufs} LUFS | 镜头 {len(shots)} 个 时长 {lens} | 静态 {statics}")
    print("降级:", edl.get("降级") or "无")
    print("检查:", "全部通过" if not fails else "\n  - " + "\n  - ".join(fails))
    print("对照图:", sheet)
    return not fails


if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1], sys.argv[2]) else 1)
