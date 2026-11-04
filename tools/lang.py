"""语言表：配音音色、识别语言、字体、分词方式。config.json 的 "语言" 填这里的键（默认 zh）。"""
import re

F = "C:/Windows/Fonts/"
LANGS = {
    #       whisper  分词     热门男声(第1个为默认)                                   热门女声                                       字体
    "zh":  ("zh", "字", ["zh-CN-YunxiNeural", "zh-CN-YunjianNeural", "zh-CN-YunyangNeural"], ["zh-CN-XiaoxiaoNeural", "zh-CN-XiaoyiNeural"], F + "msyhbd.ttc"),
    "en":  ("en", "词", ["en-US-AndrewNeural", "en-US-BrianNeural", "en-US-GuyNeural"], ["en-US-AvaNeural", "en-US-EmmaNeural", "en-US-JennyNeural"], F + "seguibl.ttf"),
    "en-GB": ("en", "词", ["en-GB-RyanNeural", "en-GB-ThomasNeural"], ["en-GB-SoniaNeural", "en-GB-LibbyNeural"], F + "seguibl.ttf"),
    "ja":  ("ja", "字", ["ja-JP-KeitaNeural"], ["ja-JP-NanamiNeural"], F + "YuGothB.ttc"),
    "ko":  ("ko", "词", ["ko-KR-InJoonNeural", "ko-KR-HyunsuMultilingualNeural"], ["ko-KR-SunHiNeural"], F + "malgunbd.ttf"),
    "es":  ("es", "词", ["es-MX-JorgeNeural", "es-ES-AlvaroNeural"], ["es-MX-DaliaNeural", "es-ES-ElviraNeural"], F + "seguibl.ttf"),
    "pt":  ("pt", "词", ["pt-BR-AntonioNeural"], ["pt-BR-FranciscaNeural", "pt-BR-ThalitaMultilingualNeural"], F + "seguibl.ttf"),
    "fr":  ("fr", "词", ["fr-FR-HenriNeural", "fr-FR-RemyMultilingualNeural"], ["fr-FR-DeniseNeural", "fr-FR-VivienneMultilingualNeural"], F + "seguibl.ttf"),
    "de":  ("de", "词", ["de-DE-ConradNeural", "de-DE-KillianNeural"], ["de-DE-KatjaNeural", "de-DE-SeraphinaMultilingualNeural"], F + "seguibl.ttf"),
    "it":  ("it", "词", ["it-IT-DiegoNeural", "it-IT-GiuseppeMultilingualNeural"], ["it-IT-IsabellaNeural", "it-IT-ElsaNeural"], F + "seguibl.ttf"),
    "ru":  ("ru", "词", ["ru-RU-DmitryNeural"], ["ru-RU-SvetlanaNeural"], F + "seguibl.ttf"),
    "id":  ("id", "词", ["id-ID-ArdiNeural"], ["id-ID-GadisNeural"], F + "seguibl.ttf"),
    "ms":  ("ms", "词", ["ms-MY-OsmanNeural"], ["ms-MY-YasminNeural"], F + "seguibl.ttf"),
    "vi":  ("vi", "词", ["vi-VN-NamMinhNeural"], ["vi-VN-HoaiMyNeural"], F + "seguibl.ttf"),
    "fil": ("tl", "词", ["fil-PH-AngeloNeural"], ["fil-PH-BlessicaNeural"], F + "seguibl.ttf"),
    "th":  ("th", "整句", ["th-TH-NiwatNeural"], ["th-TH-PremwadeeNeural"], F + "LeelawUI.ttf"),
}
PUNCT = re.compile(r"[\s，。！？、；：,.!?;:“”\"'‘’（）()《》…·\-—¿¡«»]")
BREAK = set("，、；：,;:。！？.!?…")


def info(code):
    if code not in LANGS:
        raise SystemExit(f"不支持的语言 {code}，可选：{', '.join(LANGS)}")
    w, mode, male, female, font = LANGS[code]
    return dict(whisper=w, mode=mode, spaced=mode == "词", male=male, female=female, font=font)


def units(text, code="zh"):
    """把一句拆成计时单位：中文/日文/泰文按字，其余按词。返回 [(单位, 前面是否有停顿标点)]。"""
    out, brk = [], True
    if info(code)["spaced"]:
        for tok in text.split():
            core = PUNCT.sub("", tok).lower()
            if core:
                out.append((core, brk))
                brk = False
            if tok and tok[-1] in BREAK:
                brk = True
        return out
    for ch in text:
        if ch in BREAK:
            brk = True
        elif not PUNCT.match(ch):
            out.append((ch, brk))
            brk = False
    return out


def join(us, code="zh"):
    return (" " if info(code)["spaced"] else "").join(us)
