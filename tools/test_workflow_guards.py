"""Regression checks for cropped Malay subtitles and stills in moving-only edits."""
from contextlib import redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest

from caption_layout import fit_captions, safe_width, width
from common import load, save
import match
import render


def cfg():
    return {"任务类型":"非产品类","语言":"ms","画面模式":"全动态",
            "画布":{"宽":1080,"高":1920,"帧率":30},"排除标签":[],"配乐":{},
            "规则":{"最短镜头秒":1.5,"最长镜头秒":4.0,"切点提前帧":2,
                    "动态阈值":2.0,"静态镜头上限":5,"静态推近":1.12,
                    "字幕安全宽度比例":0.86}}


def timed(text):
    words=[{"word":w,"start":.06+i*.4,"end":.36+i*.4} for i,w in enumerate(text.split())]
    return {"lang":"ms","sentences":[{"text":text,"start":words[0]["start"],"end":words[-1]["end"],"words":words}]}


class CaptionTests(unittest.TestCase):
    def test_wide_malay_is_split_without_lost_words_or_bad_timing(self):
        text="Untuk membersihkan permukaan dengan cepat"
        ts=timed(text)
        caption={"文本":text,"起":.06,"止":2.0}
        self.assertGreater(width(caption,"ms"),1080)
        result=fit_captions([caption],ts,"ms",cfg())
        self.assertGreater(len(result),1)
        self.assertEqual(" ".join(c["文本"] for c in result),text)
        self.assertEqual(result[0]["起"],caption["起"])
        self.assertEqual(result[-1]["止"],caption["止"])
        self.assertTrue(all(width(c,"ms")<=safe_width(cfg()) for c in result))
        self.assertTrue(all(a["止"]==b["起"] for a,b in zip(result,result[1:])))

    def test_short_caption_is_unchanged(self):
        caption={"文本":"Kain bersih","起":0,"止":1.5}
        self.assertEqual(fit_captions([caption],{},"ms",cfg()),[caption])

    def test_unaligned_long_caption_fails_instead_of_guessing_times(self):
        caption={"文本":"Untuk membersihkan permukaan dengan cepat","起":.06,"止":2.0}
        with self.assertRaisesRegex(ValueError,"时间戳不匹配"):
            fit_captions([caption],timed("Different speech with other words"),"ms",cfg())

    def test_indivisible_long_token_scales_inside_safe_width(self):
        text="RefrigeratorCleaningRoutine"*2
        result=fit_captions([{"文本":text,"起":.06,"止":2}],timed(text),"ms",cfg())
        self.assertLess(result[0]["字号"],60)
        self.assertGreaterEqual(result[0]["字号"],24)
        self.assertLessEqual(width(result[0],"ms"),safe_width(cfg()))

    def test_shaped_language_keeps_its_line_intact(self):
        text="清洁冰箱表面保持食品储存区域整洁"
        result=fit_captions([{"文本":text,"起":0,"止":3}],{},"zh",cfg())
        self.assertEqual(result[0]["文本"],text)
        self.assertLessEqual(width(result[0],"zh"),safe_width(cfg()))


class MotionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="remix_regression_")
        self.proj=Path(self.temp.name)
        self.config=cfg()
        self.config['产品角标']={"文件":"test-product.png","宽":200,"右距":30,"底距":100}
        self.timestamp=self.proj/'timestamps.json'
        save(self.timestamp,timed("Untuk membersihkan permukaan dengan cepat"))
        self.beats={"版本":"S1_AI","草稿名":"test","总时长":3,
            "时间戳":str(self.timestamp),"口播":"voice.wav",
            "段":[{"句":[0],"必需":["擦拭"],"关键词":[]}]}
        self.candidate={"id":"A01","源文件":"live.mp4","源宽":720,"源高":1280,
            "入":0,"出":4,"时长":4,"可用":True,"运动量":6,
            "裁切像素宽":720,"裁切":{"x0":0,"y0":0,"w":1,"h":1}}
        self.sync()

    def tearDown(self):
        self.temp.cleanup()

    def sync(self):
        save(self.proj/'config.json',self.config)
        save(self.proj/'beats.json',self.beats)
        save(self.proj/'work/candidates.json',{"窗":[self.candidate]})
        save(self.proj/'work/tags.json',{"A01":["擦拭"]})

    def test_moving_edit_keeps_overlay_and_fitted_subtitles(self):
        with redirect_stdout(io.StringIO()):
            match.main(self.proj,'beats.json')
        edl=load(self.proj/'work/EDL_S1_AI.json')
        self.assertEqual(edl['产品角标'],self.config['产品角标'])
        self.assertEqual(edl['画面模式'],'全动态')
        self.assertEqual(edl['镜头'][0]['推近'],1)
        self.assertTrue(all(width(c,'ms')<=safe_width(self.config) for c in edl['字幕']))

    def test_moving_mode_overrides_old_static_allowance(self):
        self.candidate['运动量']=0
        self.sync()
        with self.assertRaisesRegex(SystemExit,"缺镜头"):
            match.main(self.proj,'beats.json')

    def test_moving_mode_rejects_full_frame_product_card(self):
        self.beats['段'][0]['用图']='product.png'
        self.sync()
        with self.assertRaisesRegex(SystemExit,"全动态模式"):
            match.main(self.proj,'beats.json')

    def test_custom_edl_cannot_bypass_still_guard(self):
        save(self.proj/'work/EDL.json',{"语言":"ms","结尾图":None,"镜头":[
            {"源文件":"baked.mp4","推近":1,"原片静帧秒":0}],"字幕":[]})
        with self.assertRaisesRegex(ValueError,"静态主画面"):
            render.main(self.proj,'EDL.json')
        self.assertFalse((self.proj/'output').exists())


if __name__=='__main__':
    unittest.main()
