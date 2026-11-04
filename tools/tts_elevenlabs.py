"""AI 口播：用 ElevenLabs 把文稿生成 MP3。key 只从环境变量 ELEVENLABS_API_KEY 读，不写进任何文件。
音色按名字找：先找“我的音色”，找不到再去公开音色库搜并加进账号。
用法: python tts_elevenlabs.py <文稿.txt> <输出.mp3> [音色名关键词=James Gao] [语速=1.0]
"""
from pathlib import Path
import json, os, sys, urllib.parse, urllib.request

KEY = os.environ.get("ELEVENLABS_API_KEY", "")
API = "https://api.elevenlabs.io"
if not KEY.startswith("sk_"):
    sys.exit("环境变量 ELEVENLABS_API_KEY 没设或不是 sk_ 开头")
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))   # 直连，不走系统代理


def call(method, path, body=None, raw=False):
    req = urllib.request.Request(API + path, method=method, data=None if body is None else json.dumps(body).encode(),
                                 headers={"xi-api-key": KEY, "Content-Type": "application/json", "Accept": "*/*"})
    try:
        with opener.open(req, timeout=120) as r:
            data = r.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"ElevenLabs {method} {path.split('?')[0]} 返回 {e.code}：{e.read().decode(errors='replace')[:400]}")
    return data if raw else json.loads(data)


script, out = Path(sys.argv[1]), Path(sys.argv[2])
name = sys.argv[3] if len(sys.argv) > 3 else "James Gao"
speed = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
lines = [l.strip() for l in script.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
text = "\n".join(lines)

mine = call("GET", "/v1/voices")["voices"]
v = next((x for x in mine if name.lower() in x["name"].lower()), None)
if v is None:
    q = urllib.parse.quote(name)
    shared = call("GET", f"/v1/shared-voices?search={q}&page_size=10").get("voices", [])
    s = next((x for x in shared if name.lower() in x["name"].lower()), None)
    if s is None:
        sys.exit(f"找不到音色“{name}”。我的音色：{[x['name'] for x in mine][:15]}")
    added = call("POST", f"/v1/voices/add/{s['public_owner_id']}/{s['voice_id']}", {"new_name": s["name"]})
    v = dict(voice_id=added["voice_id"], name=s["name"])
    print("已把公开音色加进账号:", s["name"])
print("音色:", v["name"], "| 字符数:", len(text))
audio = call("POST", f"/v1/text-to-speech/{v['voice_id']}?output_format=mp3_44100_128",
             dict(text=text, model_id="eleven_multilingual_v2",
                  voice_settings=dict(stability=0.5, similarity_boost=0.75, style=0.15, use_speaker_boost=True, speed=speed)),
             raw=True)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_bytes(audio)
sub = call("GET", "/v1/user/subscription")
print(f"已生成 {out.name} {len(audio) // 1024}KB | 剩余额度 {sub.get('character_limit', 0) - sub.get('character_count', 0)}")
