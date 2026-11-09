"""第4步 出片：同一份 EDL 生成预览 MP4（AAC + Opus 两份）和剪映草稿包。

用法: python render.py <项目目录> <EDL 文件名，如 EDL_真人版.json>
"""
from pathlib import Path
import shutil, subprocess, sys
from common import load, save, clip_geom, full_motion, static_shot
from caption_layout import fit_captions
import lang as L

FONT = "C\\:/Windows/Fonts/msyhbd.ttc"
# 大字花字：汉仪雅酷黑 95W（特粗），黄字 + 深棕粗描边 + 投影，逐字弹出
import os
KWFONT = os.environ.get("MIX_KWFONT", os.path.expandvars(r"%LOCALAPPDATA%/Microsoft/Windows/Fonts/HYYakuHei-95W.ttf")).replace("\\", "/").replace(":", "\\:")
KW_STAGGER = 0.06   # 每个字比前一个晚出现的秒数
# 大字样式库（对标视频每个大字的样式都不一样）。预览用本机字体，剪映草稿用剪映自带的近似字体和动画。
KW_FONTS = {"雅酷黑": KWFONT, "舒体": "C\\:/Windows/Fonts/FZSTK.TTF", "宋体": "C\\:/Windows/Fonts/NotoSerifSC-VF.ttf"}
KW_STYLES = {   # 字体、填充色、描边色、描边粗细、预览动画、剪映字体、剪映动画
    "花字":  dict(font="雅酷黑", fill="0xFFD21F", edge="0x3A1E08", bw=12, anim="弹跳", jy_font="优设标题黑", jy_anim="波浪弹入"),
    "砸字":  dict(font="雅酷黑", fill="0xFFFFFF", edge="0x111111", bw=12, anim="砸入", jy_font="优设标题黑", jy_anim="放大震动"),
    "宋体":  dict(font="宋体", fill="0xFFF4D6", edge="0x5A3410", bw=4, anim="上滑", jy_font="思源粗宋", jy_anim="向上弹入", glow=True),
    "重点":  dict(font="雅酷黑", fill="0xFFFFFF", edge="0x111111", bw=10, anim="弹跳", jy_font="优设标题黑", jy_anim="弹入跳动", hi="0xFFD21F"),
    "竖排":  dict(font="雅酷黑", fill="0xFFB01F", edge="0x2A1405", bw=11, anim="下落", jy_font="庞门正道粗书体", jy_anim="逐字显影"),
}


def set_lang(code):
    """非中文：预览字幕和大字都换成该语言的字体（中文字体缺外文字形），竖排关掉。"""
    global FONT, LANG
    LANG = code
    if code != "zh":
        f = L.info(code)["font"].replace(":", "\\:")
        FONT = f
        for k in KW_FONTS:
            KW_FONTS[k] = f


LANG = "zh"


def pick_styles(kws, seed):
    """给每个大字分一种样式：开头固定“花字”，相邻不重复，竖排只给 ≤5 个字的；按草稿名定随机种子，重跑结果一样。"""
    import random
    rnd, prev, out = random.Random(seed), None, []
    for n, k in enumerate(kws):
        if k["槽"] is not None:
            out.append(None)
            continue
        n_ch = len(k["文本"].replace(" ", ""))
        pool = [s for s in KW_STYLES if s != prev and (s != "竖排" or (n_ch <= 5 and LANG in ("zh", "ja")))]
        s = "花字" if prev is None else rnd.choice(pool)
        out.append(s)
        prev = s
    return out


def kw_draw(k, W, H):
    """一个大字的 drawtext 链：逐字出现，按样式决定字体、颜色和动画。"""
    S = KW_STYLES[k["_样式"]]
    font = KW_FONTS[S["font"]]
    text = k["文本"].replace(":", "：").replace("'", "’")
    vertical = k["_样式"] == "竖排"
    mode = L.info(LANG)["mode"]
    if vertical:
        chars = list(text.replace(" ", ""))
    elif mode == "词":   # 按词弹出，词宽按字母数估
        chars = text.split()
    elif mode == "整句":   # 泰文等有上下标符号，拆字会错位，整句一起出
        chars = [text]
    else:
        chars = list(text)
    units = [0.58 if ch.isascii() else 1.0 for ch in chars] if mode == "字" or vertical else             [(0.62 * len(w) + 0.12 * sum(c.isupper() for c in w)) + (0.25 if mode == "词" else 0) for w in chars]
    base = 128 if vertical else (150 if S["anim"] == "砸入" else 132)
    fs = base if vertical else min(base, 980 / max(sum(units), 1))
    step = [fs * u + 6 for u in units]
    pos, x, y = [], (W - sum(step)) / 2, H * 0.30 - len(chars) * fs * 1.12 / 2
    for i, ch in enumerate(chars):
        pos.append((x + step[i] / 2, H * BIG_Y) if not vertical else (W * 0.80, y + fs * 1.12 * i + fs / 2))
        x += step[i]
    half = len(chars) // 2
    g = ""
    for i, (ch, (cx, cy)) in enumerate(zip(chars, pos)):
        if ch == " ":
            continue
        t0 = k["起"] + i * (KW_STAGGER if S["anim"] != "下落" else 0.09)
        q = f"clip((t-{t0:.3f})/0.25\\,0\\,1)"
        back = f"(1+2.70158*pow({q}-1\\,3)+1.70158*pow({q}-1\\,2))"
        size, dy, alpha = {
            "弹跳": (f"{fs}*{back}", f"-30*(1-{q})", "1"),
            "砸入": (f"{fs}*(2.2-1.2*{q})", "0", f"{q}"),                    # 从大往小砸下来
            "上滑": (f"{fs}", f"60*(1-{q})", f"{q}"),                          # 从下往上淡入
            "下落": (f"{fs}*{back}", f"-80*(1-{q})", f"{q}"),                  # 竖排逐字往下落
        }[S["anim"]]
        fill = S.get("hi") if S.get("hi") and i >= half else S["fill"]
        en = f"enable='between(t,{t0:.3f},{k['止']})'"
        common = (f"fontfile='{font}':text='{ch}':fontsize='max(1\\,{size})':x={cx:.1f}-text_w/2:"
                  f"y={cy:.1f}-text_h/2+{dy}:alpha='{alpha}':{en}")
        if S.get("glow"):   # 宋体发光：先画一层宽描边的暖色光晕
            g += f",drawtext={common}:fontcolor={S['fill']}@0.0:borderw=22:bordercolor=0xFFB040@0.35"
        g += f",drawtext={common}:fontcolor={fill}:borderw={S['bw']}:bordercolor={S['edge']}:shadowx=0:shadowy=8:shadowcolor=black@0.6"
    return g
BIG_Y, LIST_Y = 0.38, (0.30, 0.39, 0.48)


def run(args):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *map(str, args)], check=True)


def product_overlay(edl, canvas_width, canvas_height):
    corner = edl.get("产品角标")
    if not corner:
        return None
    from PIL import Image

    path = Path(corner["文件"])
    with Image.open(path) as image:
        if image.format != "PNG":
            raise ValueError(f"产品角标需要 PNG: {path}")
        low, high = image.convert("RGBA").getchannel("A").getextrema()
        if low == 255 or high == 0:
            raise ValueError(f"产品角标需要透明背景且商品可见: {path}")
        iw, ih = image.size
    w, right, bottom = (int(corner[k]) for k in ("宽", "右距", "底距"))
    h = max(2, round(w * ih / iw / 2) * 2)
    x, y = canvas_width - right - w, canvas_height - bottom - h
    if w < 2 or min(x, y, right, bottom) < 0:
        raise ValueError("产品角标超出画布")
    return path, x, y, w, h


def preview(edl, cfg, out):
    W, H, FPS = cfg["画布"]["宽"], cfg["画布"]["高"], cfg["画布"]["帧率"]
    TL = cfg["规则"]["转场时长"]
    src_dir, sfx_dir = Path(cfg["素材目录"]), Path(cfg["音效目录"])
    dur, shots, img = edl["总时长"], edl["镜头"], edl["结尾图"]
    xf = TL["叠化"] if img else 0
    inputs, chains = [], []
    for i, s in enumerate(shots):
        n = round(s["止"] * FPS) - round(s["起"] * FPS)
        extra = xf if (img and i == len(shots) - 1) else 0
        if s.get("占位"):   # 预演：缺镜头的段放深色卡片，写明缺什么
            take = s["止"] - s["起"] + extra
            inputs += ["-f", "lavfi", "-t", round(take + 0.15, 3), "-i", f"color=c=0x2A2620:s={W}x{H}:r={FPS}"]
            chains.append(f"[{i}:v]setpts=PTS-STARTPTS,drawtext=fontfile='{FONT}':text='{s['文本']}':fontsize=64:"
                          f"fontcolor=0xFF5A4A:x=(w-text_w)/2:y=h*0.55-text_h/2,trim=end_frame={n + round(extra * FPS)},setsar=1[v{i}]")
            continue
        take = min(s["止"] - s["起"] + extra, s["窗出"] - s["源入点"])
        c, sw, sh = s["裁切"], s["源宽"], s["源高"]
        cw, ch = round(c["w"] * sw / 2) * 2, round(c["h"] * sh / 2) * 2
        cx, cy = round(c["x0"] * sw), round(c["y0"] * sh)
        wc = s.get("宽裁切")
        if wc:   # 对标做法：宽一些的清晰画面放中间，上下用同一镜头的 9:16 裁切放大 + 模糊补满
            ww, wh = round(wc["w"] * sw / 2) * 2, round(wc["h"] * sh / 2) * 2
            wx, wy = round(wc["x0"] * sw), round(wc["y0"] * sh)
            chain = (f"[{i}:v]fps={FPS},setpts=PTS-STARTPTS,split[b{i}][f{i}];"
                     f"[b{i}]crop={cw}:{ch}:{cx}:{cy},scale={W // 4}:{H // 4},gblur=sigma=12,scale={W}:{H},eq=brightness=-0.06[bg{i}];"
                     f"[f{i}]crop={ww}:{wh}:{wx}:{wy},scale={W}:-2:flags=lanczos[fg{i}];"
                     f"[bg{i}][fg{i}]overlay=0:(H-h)/2")
        else:
            chain = f"[{i}:v]fps={FPS},setpts=PTS-STARTPTS,crop={cw}:{ch}:{cx}:{cy},scale={W}:{H}:flags=lanczos"
        chain += ",eq=" + s.get("调色", "brightness=0")
        if s["推近"] != 1.0:
            m = round(take * FPS)
            chain += (f",zoompan=z='1+({s['推近']}-1)*on/{max(m - 1, 1)}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2'"
                      f":d=1:s={W}x{H}:fps={FPS}")
        chain += f",trim=end_frame={n + round(extra * FPS)},setsar=1[v{i}]"
        inputs += ["-ss", s["源入点"], "-t", round(take + 0.15, 3), "-i", src_dir / s["源文件"]]
        chains.append(chain)
    ns = len(shots)
    g = ";\n".join(chains)
    g += ";\n" + "".join(f"[v{i}]" for i in range(ns)) + f"concat=n={ns}:v=1:a=0,tpad=stop_mode=clone:stop_duration={dur}[cat]"
    nxt = ns
    if img:
        iw, ih = map(int, subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of",
                                                   "csv=p=0", img["文件"]]).decode().split(","))
        img_w = round(iw * H / ih / 2) * 2
        span = (img_w - W) / 2
        pan = min(img["平移"], span / (W / 2))
        L = dur - img["起"] + xf
        x_expr = f"{span}-{pan}*{W / 2}+{pan * W}*t/{L}"
        inputs += ["-loop", "1", "-framerate", FPS, "-t", round(L + 0.2, 3), "-i", img["文件"]]
        g += (f";\n[{nxt}:v]scale={img_w}:{H}:flags=lanczos,crop={W}:{H}:x='{x_expr}':y=0,setsar=1,format=yuva420p,"
              f"fade=t=in:st=0:d={xf}:alpha=1,setpts=PTS-STARTPTS+{img['起'] - xf}/TB[img]")
        g += ";\n[cat][img]overlay=eof_action=pass:shortest=0[base]"
        nxt += 1
    else:
        g += ";\n[cat]null[base]"
    fx = []
    for s in shots:
        t, tr = s["止"], s["出转场"]
        if tr == "闪白":
            fx.append(f"eq=brightness='0.85*max(0\\,1-abs(t-{t})/{TL[tr] / 2})':eval=frame")
        elif tr == "模糊":
            h = TL[tr] / 2
            fx += [f"gblur=sigma=14:enable='between(t,{t - h},{t + h})'", f"gblur=sigma=22:enable='between(t,{t - h / 2},{t + h / 2})'"]
    g += ";\n[base]" + (",".join(fx) if fx else "null") + "[scene]"
    base_label = "scene"
    corner = product_overlay(edl, W, H)
    if corner:
        path, x, y, w, h = corner
        inputs += ["-i", path]
        g += (f";\n[{nxt}:v]scale={w}:{h}:flags=lanczos,format=rgba[product];\n"
              f"[scene][product]overlay=x={x}:y={y}:eof_action=repeat:shortest=0[with_product]")
        nxt += 1
        base_label = "with_product"
    g += f";\n[{base_label}]null"
    for c in edl["字幕"]:
        safe = c["文本"].replace("'", "’").replace(":", "：" if LANG in ("zh", "ja") else r"\:").replace("%", r"\%")
        subtitle_style = "fontsize=60:fontcolor=white:borderw=4"
        if "字号" in c:
            subtitle_style = subtitle_style.replace("fontsize=60", f"fontsize={c['字号']}")
        g += (f",drawtext=fontfile='{FONT}':text='{safe}':{subtitle_style}:bordercolor=black@0.85:"
              f"x=(w-text_w)/2:y=h*0.74-text_h/2:enable='between(t,{c['起']},{c['止']})'")
    for k in edl["关键词"]:
        if k["槽"] is None:   # 大字：按分到的样式逐字出现（样式见 KW_STYLES）
            g += kw_draw(k, W, H)
            continue
        p = f"clip((t-{k['起']})/0.25\\,0\\,1)"
        base = 120 if k["槽"] is None else 96   # 对标：要点标题中等大小，不压满屏
        size = f"max(1\\,{base}*(1+2.70158*pow({p}-1\\,3)+1.70158*pow({p}-1\\,2)))"
        x = "(w-text_w)/2" if k["槽"] is None else "w*0.22"
        y = f"h*{BIG_Y}-text_h/2" if k["槽"] is None else f"h*{LIST_Y[k['槽']]}-text_h/2"
        safe = k["文本"].replace("'", "’")
        g += (f",drawtext=fontfile='{FONT}':text='{safe}':fontsize='{size}':fontcolor=white:borderw=8:"
              f"bordercolor=0xFFC81E:shadowx=0:shadowy=6:shadowcolor=black@0.7:x={x}:y={y}:enable='between(t,{k['起']},{k['止']})'")
    g += ",format=yuv420p[vout]"
    M = edl["配乐"]
    vi, mi = nxt, nxt + 1
    inputs += ["-i", edl["口播"], "-i", sfx_dir / M["文件"]]
    g += (f";\n[{vi}:a]atrim=0:{dur},asetpts=PTS-STARTPTS,apad=whole_dur={dur},aresample=48000,"
          f"afade=t=out:st={dur - 0.15}:d=0.15,asplit=2[voice][key]")
    g += (f";\n[{mi}:a]atrim={M['入点']}:{M['入点'] + dur},asetpts=PTS-STARTPTS,aresample=48000,volume={M['增益']}dB,"
          f"afade=t=in:d=0.05,afade=t=out:st={dur - 0.6}:d=0.6[mraw]")
    g += ";\n[mraw][key]sidechaincompress=threshold=0.03:ratio=4:attack=20:release=250:makeup=1:level_sc=1[music]"
    labels = ["[voice]", "[music]"]
    for k, e in enumerate(edl["音效"]):
        S = cfg["音效"][e["类型"]]
        inputs += ["-i", sfx_dir / S["文件"]]
        ms = max(0, round(e["时间"] * 1000))
        g += (f";\n[{mi + 1 + k}:a]atrim={S['入点']}:{S['入点'] + S['时长']},asetpts=PTS-STARTPTS,aresample=48000,"
              f"volume={S['增益']}dB,afade=t=out:st={S['时长'] - S['淡出']}:d={S['淡出']},adelay={ms}|{ms},apad[s{k}]")
        labels.append(f"[s{k}]")
    g += f";\n{''.join(labels)}amix=inputs={len(labels)}:duration=first:normalize=0,loudnorm=I=-11:TP=-1:LRA=7,aresample=48000[aout]"
    (out / "preview_filter.txt").write_text(g, encoding="utf-8")
    mp4 = out / f"{edl['草稿名']}_预览.mp4"
    run([*inputs, "-/filter_complex", out / "preview_filter.txt", "-map", "[vout]", "-map", "[aout]", "-t", dur,
         "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", mp4])
    run(["-i", mp4, "-c:v", "copy", "-c:a", "libopus", "-b:a", "160k", "-ac", "2", out / f"{edl['草稿名']}_预览_VSCode可播.mp4"])
    return mp4


def draft(edl, cfg, out):
    import pyJianYingDraft as j
    from pyJianYingDraft import TransitionType, TextIntro, KeyframeProperty as KP, FontType
    W, H, FPS = cfg["画布"]["宽"], cfg["画布"]["高"], cfg["画布"]["帧率"]
    TL = cfg["规则"]["转场时长"]
    src_dir, sfx_dir = Path(cfg["素材目录"]), Path(cfg["音效目录"])
    media = out / "素材"
    media.mkdir(exist_ok=True)
    for f in {s["源文件"] for s in edl["镜头"] if not s.get("占位")}:
        if not (media / f).exists():
            shutil.copy2(src_dir / f, media / f)
    for f in {cfg["音效"][e["类型"]]["文件"] for e in edl["音效"]} | {edl["配乐"]["文件"]}:
        shutil.copy2(sfx_dir / f, media / Path(f).name)
    shutil.copy2(edl["口播"], media / "口播.wav")
    img = edl["结尾图"]
    if img:
        shutil.copy2(img["文件"], media / Path(img["文件"]).name)
    for f in ("安装到剪映.py", "安装到剪映.cmd"):
        shutil.copy2(Path(cfg.get("剪映安装器目录") or Path(__file__).parent / "剪映安装器") / f, out / f)

    us = lambda s: round(s * j.SEC)
    db = lambda g: round(10 ** (g / 20), 4)
    dur = edl["总时长"]
    (out / "剪映草稿").mkdir(exist_ok=True)
    d = j.DraftFolder(str(out / "剪映草稿")).create_draft(edl["草稿名"], W, H, FPS, allow_replace=True)
    d.append_track(j.TrackSpec(j.TrackType.video, name="实拍画面"))
    holes = []
    for s in edl["镜头"]:
        if s.get("占位"):   # 剪映里留空，另起一条文字轨写缺什么，补到素材后直接拖进空位
            holes.append(s)
            continue
        k, tx, ty = clip_geom(s["裁切"], s["源宽"], s["源高"], W, H)
        a, n = us(s["起"]), us(s["止"]) - us(s["起"])
        seg = j.VideoSegment(j.VideoMaterial(str(media / s["源文件"])), j.Timerange(a, n),
                             source_timerange=j.Timerange(us(s["源入点"]), n), volume=0,
                             clip_settings=j.ClipSettings(scale_x=k, scale_y=k, transform_x=tx, transform_y=ty))
        if s["推近"] != 1.0:
            k1, tx1, ty1 = clip_geom(s["裁切"], s["源宽"], s["源高"], W, H, s["推近"])
            for prop, v0, v1 in ((KP.uniform_scale, k, k1), (KP.position_x, tx, tx1), (KP.position_y, ty, ty1)):
                seg.add_keyframe(prop, 0, v0)
                seg.add_keyframe(prop, n, v1)
        if s["出转场"]:
            seg.add_transition(getattr(TransitionType, s["出转场"]), duration=us(TL[s["出转场"]]))
        d.add_segment(seg, track="实拍画面")
    if img:
        mat = j.VideoMaterial(str(media / Path(img["文件"]).name))
        iw, ih = mat.width, mat.height
        s0 = min(W / iw, H / ih)
        k = H / (ih * s0)
        span = (iw * s0 * k - W) / 2 / (W / 2)
        pan = min(img["平移"], span)
        n = us(dur) - us(img["起"])
        seg = j.VideoSegment(mat, j.Timerange(us(img["起"]), n),
                             clip_settings=j.ClipSettings(scale_x=k, scale_y=k, transform_x=pan))
        seg.add_keyframe(KP.position_x, 0, pan)
        seg.add_keyframe(KP.position_x, n, -pan)
        d.add_segment(seg, track="实拍画面")

    corner = product_overlay(edl, W, H)
    if corner:
        path, x, y, w, h = corner
        local_png = media / path.name
        if path.resolve() != local_png.resolve():
            shutil.copy2(path, local_png)
        mat = j.VideoMaterial(str(local_png))
        fit = min(W / mat.width, H / mat.height)
        d.append_track(j.TrackSpec(j.TrackType.video, name="产品PNG角标"))
        seg = j.VideoSegment(mat, j.Timerange(0, us(dur)),
                             clip_settings=j.ClipSettings(
                                 scale_x=w / (mat.width * fit), scale_y=h / (mat.height * fit),
                                 transform_x=(2*x + w) / W - 1, transform_y=1 - (2*y + h) / H))
        d.add_segment(seg, track="产品PNG角标")

    def place(kind, prefix, segs):
        ends = []
        for seg, a, b in segs:
            for i, e in enumerate(ends):
                if a >= e:
                    break
            else:
                i = len(ends)
                ends.append(0)
                d.append_track(j.TrackSpec(kind, name=f"{prefix}{i + 1}"))
            ends[i] = b
            d.add_segment(seg, track=f"{prefix}{i + 1}")

    d.append_track(j.TrackSpec(j.TrackType.audio, name="原口播"))
    voice = j.AudioMaterial(str(media / "口播.wav"))
    vd = min(us(dur), voice.duration)
    d.add_segment(j.AudioSegment(voice, j.Timerange(0, vd), source_timerange=j.Timerange(0, vd)), track="原口播")
    M = edl["配乐"]
    d.append_track(j.TrackSpec(j.TrackType.audio, name="配乐"))
    m = j.AudioSegment(j.AudioMaterial(str(media / Path(M["文件"]).name)), j.Timerange(0, us(dur)),
                       source_timerange=j.Timerange(us(M["入点"]), us(dur)), volume=db(M["增益"] - M["压低"]))
    m.add_fade("0.05s", "0.6s")
    d.add_segment(m, track="配乐")
    segs = []
    for e in edl["音效"]:
        S = cfg["音效"][e["类型"]]
        a = us(max(0, e["时间"]))
        seg = j.AudioSegment(j.AudioMaterial(str(media / S["文件"])), j.Timerange(a, us(S["时长"])),
                             source_timerange=j.Timerange(us(S["入点"]), us(S["时长"])), volume=db(S["增益"]))
        seg.add_fade(0, f"{S['淡出']}s")
        segs.append((seg, a, a + us(S["时长"])))
    place(j.TrackType.audio, "音效", segs)
    segs = []
    for c in edl["字幕"]:
        subtitle_style = j.TextStyle(size=10.5, bold=True, align=1)
        subtitle_style.size *= c.get("字号", 60) / 60
        seg = j.TextSegment(c["文本"], j.Timerange(us(c["起"]), us(c["止"]) - us(c["起"])), font=FontType.抖音美好体,
                            style=subtitle_style, border=j.TextBorder(width=60),
                            clip_settings=j.ClipSettings(transform_y=-0.40))
        segs.append((seg, us(c["起"]), us(c["止"])))
    place(j.TrackType.text, "句字幕", segs)
    segs = []
    for kw in edl["关键词"]:
        big = kw["槽"] is None
        cs = j.ClipSettings(transform_y=2 * (0.5 - BIG_Y)) if big else j.ClipSettings(transform_x=-0.30, transform_y=2 * (0.5 - LIST_Y[kw["槽"]]))
        S = KW_STYLES[kw["_样式"]] if big else KW_STYLES["花字"]
        rgb = lambda h: tuple(int(h[i:i + 2], 16) / 255 for i in (2, 4, 6))
        font = getattr(FontType, S["jy_font"], FontType.优设标题黑)
        anim = getattr(TextIntro, S["jy_anim"], TextIntro.弹入) if big else TextIntro.弹入
        text = "\n".join(kw["文本"].replace(" ", "")) if big and kw["_样式"] == "竖排" else kw["文本"]
        if big and kw["_样式"] == "竖排":
            cs = j.ClipSettings(transform_x=0.60, transform_y=0.35)
        seg = j.TextSegment(text, j.Timerange(us(kw["起"]), us(kw["止"]) - us(kw["起"])), font=font,
                            style=j.TextStyle(size=22 if big else 15, bold=True, align=1 if big else 0, color=rgb(S["fill"])),
                            border=j.TextBorder(width=80, color=rgb(S["edge"])), clip_settings=cs)
        seg.add_animation(anim, duration="0.5s")
        segs.append((seg, us(kw["起"]), us(kw["止"])))
    place(j.TrackType.text, "关键词", segs)
    if holes:
        d.append_track(j.TrackSpec(j.TrackType.text, name="缺镜头标记"))
        for s in holes:
            d.add_segment(j.TextSegment(s["文本"], j.Timerange(us(s["起"]), us(s["止"]) - us(s["起"])),
                                        style=j.TextStyle(size=9, bold=True, align=1, color=(1.0, 0.35, 0.29)),
                                        clip_settings=j.ClipSettings(transform_y=-0.10)), track="缺镜头标记")
    d.save()


def main(proj, edl_name):
    proj = Path(proj)
    cfg = load(proj / "config.json")
    edl = load(proj / "work" / edl_name)
    if full_motion(cfg, edl) and (edl.get("结尾图") or any(static_shot(s, cfg) for s in edl["镜头"] if not s.get("占位"))):
        raise ValueError("全动态模式含静态主画面，请换连续视频；产品PNG可保留在角标轨")
    timestamps = load(edl["时间戳"]) if edl.get("时间戳") else {}
    edl["字幕"] = fit_captions(edl["字幕"], timestamps, edl.get("语言", "zh"), cfg)
    set_lang(edl.get("语言", "zh"))
    for k, s in zip(edl["关键词"], pick_styles(edl["关键词"], edl["草稿名"])):
        k["_样式"] = s
    print("大字样式:", [(k["文本"], k["_样式"]) for k in edl["关键词"] if k["_样式"]])
    out = proj / "output" / edl["版本"]
    out.mkdir(parents=True, exist_ok=True)
    if not cfg.get("音效目录"):
        cfg["音效目录"] = str(Path(__file__).resolve().parent.parent / "音效库")
    sfx_dir = Path(cfg["音效目录"])
    if not (sfx_dir / edl["配乐"]["文件"]).exists() and not cfg.get("音效目录_自定义"):
        subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "get_sfx.py")])
    miss = [e["类型"] for e in edl["音效"] if not (sfx_dir / cfg["音效"][e["类型"]]["文件"]).exists()]
    edl["音效"] = [e for e in edl["音效"] if e["类型"] not in miss]
    if not (sfx_dir / edl["配乐"]["文件"]).exists():   # 没放配乐：用静音占位，剪映里自己加
        mute = out / "_无配乐静音.wav"
        run(["-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", edl["总时长"] + 1, mute])
        edl["配乐"] = dict(edl["配乐"], 文件=str(mute.resolve()), 入点=0)
        miss.append("配乐")
    if miss:
        print("音效库里缺这些文件，已跳过:", sorted(set(miss)))
    mp4 = preview(edl, cfg, out)
    draft(edl, cfg, out)
    save(out / "编辑决定表.json", edl)
    print("出片", mp4)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
