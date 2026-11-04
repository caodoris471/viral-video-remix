"""AI 口播（免费）：edge-tts 生成配音，再交给 voice_prep 对齐出时间戳。

用法: python tts_edge.py <文稿.txt> <输出mp3> [--lang=zh] [--voice=音色] [--rate=+25%]
不写 --voice 就用该语言的默认男声（中文=云希）。列出某语言的热门音色: python tts_edge.py --list --lang=en
"""
import asyncio, sys
import edge_tts
import lang as L


def opt(name, default):
    return next((x.split("=", 1)[1] for x in sys.argv if x.startswith(f"--{name}=")), default)


async def main(txt, out, voice, rate):
    text = open(txt, encoding="utf-8").read().strip()
    await edge_tts.Communicate(text, voice, rate=rate).save(out)
    print("已生成", out, "| 音色", voice, "| 语速", rate)


if __name__ == "__main__":
    code = opt("lang", "zh")
    li = L.info(code)
    if "--list" in sys.argv:
        print("男声:", ", ".join(li["male"]), "\n女声:", ", ".join(li["female"]))
        sys.exit()
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) < 2:
        sys.exit(__doc__)
    asyncio.run(main(a[0], a[1], opt("voice", li["male"][0]), opt("rate", "+25%" if code == "zh" else "+10%")))
