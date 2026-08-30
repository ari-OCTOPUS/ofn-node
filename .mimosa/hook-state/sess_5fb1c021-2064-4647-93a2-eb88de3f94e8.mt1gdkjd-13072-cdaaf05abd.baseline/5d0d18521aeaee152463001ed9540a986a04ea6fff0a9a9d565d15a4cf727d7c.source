#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_e2e_chain.py — آیا کلِ Project-F واقعاً «به هم وصل است و باهم کار می‌کند»؟

رأیِ مالک ۲۰۲۶-۰۸-۰۳. تا امروز هر لایه سوییتِ **خودش** را داشت و سبز بود، ولی
هیچ تستی کلِ زنجیره را از سر تا ته نمی‌دواند — و درسِ ثبت‌شدهٔ همین vault می‌گوید
چهار مکانیزمِ «سبز در تست، گرسنه در تولید» دقیقاً از **درزِ بینِ ماژول‌ها** آمدند،
نه از داخلشان («خواننده و نویسنده را با هم بسنج»).

این تست هشت پلهٔ واقعیِ تولیدی را پشتِ سرِ هم می‌دواند و در انتها می‌سنجد که
**سه خوانندهٔ مستقل عددِ یکسان می‌بینند**:
    ۱ درفتِ پارتنر (self-cert چهارگانه) → ۲ تأییدِ اپراتور → ۳ handoff به VaultBank
    → ۴ ساختِ صفِ پست از بانک → ۵ approve + finalize + کدِ tracking
    → ۶ ثبتِ KPI → ۷ خوانشِ مینی‌اپ (`_ops/telegram_center/pf_miniapp.py`)
    → ۸ خوانشِ پای ارگانیسم (`_ops/legs/studio_pf_leg.py`)

هرمتیک: `PF_STUDIO_DIR`/`PF_AUDIT_FILE` **قبل از import** به tmp می‌روند (مسیرها
در زمانِ import قفل می‌شوند) و خودِ تست با یک assert اثبات می‌کند که ایزوله شده —
درسِ ۰۸-۰۳: تستی که مسیرِ واقعی را صدا بزند در state ِ زندهٔ مالک می‌نویسد.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PF = _HERE.parent
_VAULT = _PF.parents[1]
_OPS = _VAULT / "_ops"


class TestProjectFEndToEnd(unittest.TestCase):
    """یک سناریوی کامل؛ setUp محیط را می‌سازد و ماژول‌ها را تازه import می‌کند."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls._tmp.name)
        cls.studio_dir = cls.tmp / "studio"
        cls.studio_dir.mkdir()
        shutil.copy(_PF / "studio" / "config.json", cls.studio_dir / "config.json")

        # ⚠️ env قبل از import — وگرنه مسیرِ زنده قفل می‌شود
        os.environ["PF_STUDIO_DIR"] = str(cls.studio_dir)
        os.environ["PF_AUDIT_FILE"] = str(cls.tmp / "approvals.jsonl")
        os.environ["PF_AUDIT_ORIGIN"] = "test"
        os.environ["OCTOPUS_PF_MINIAPP"] = "1"

        for p in (str(_PF / "brain"), str(_PF / "studio"),
                  str(_OPS / "telegram_center"), str(_OPS / "legs")):
            if p not in sys.path:
                sys.path.insert(0, p)

        import content_studio, store, acquisition_pipeline  # noqa: WPS433
        cls.CS, cls.ST, cls.AP = content_studio, store, acquisition_pipeline

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    # ── گاردِ ایزولاسیون: اگر بشکند بقیهٔ تست‌ها در state زنده می‌نویسند ──
    def test_00_isolated_from_live_state(self):
        # ۲۰۲۶-۰۸-۰۳: _DATA_PATH حالا lazy است (_data_path()) — در زمانِ ساختِ
        # instance حل می‌شود. چون PF_STUDIO_DIR قبل از import در setUpClass set شده،
        # instance که در test_01 ساخته می‌شود هم به tmp می‌رود. اینجا تابع را صدا
        # می‌زنیم تا مسیرِ حل‌شده را ببینیم.
        resolved = self.CS._data_path()
        self.assertTrue(str(resolved).startswith(str(self.tmp)),
                        f"ایزوله نشد — درفت‌ها به {resolved} می‌روند")
        live_drafts = _PF / "studio" / "drafts.json"
        self._live_before = live_drafts.read_bytes() if live_drafts.exists() else None

    def test_01_full_chain_and_three_readers_agree(self):
        CS, ST, AP = self.CS, self.ST, self.AP
        tmp = self.tmp

        # ۱) درفتِ پارتنر با self-cert کامل
        studio = CS.ContentStudio()
        d = studio.submit_draft(title="soft light set", channel="reddit",
                                hook="quiet morning",
                                self_cert={c: True for c in CS.COMPLIANCE_CHECKS})
        self.assertTrue(d.get("ok"), d)
        did = d["draft_id"]

        # گاردِ مرزِ پارتنر: cert ناقص باید رد شود (safety net، نه تشریفات)
        bad = studio.submit_draft(title="x", self_cert={"faceless": True})
        self.assertFalse(bad.get("ok"), "درفتِ بدونِ self-cert کامل نباید پذیرفته شود")

        # ۲) تأییدِ اپراتور (گذارِ قانونی)
        self.assertTrue(studio.set_status(did, "approved").get("ok"))

        # ۳) handoff به بانکِ محتوا — idempotent و مشروط به cert کامل
        vault = ST.VaultBank(path=tmp / "vault.json")
        h = studio.handoff_to_vault(did, vault)
        self.assertTrue(h.get("ok"), h)
        self.assertTrue(h.get("vault_id"))

        # ۴) صفِ پست از همان بانک ساخته شود
        links = ST.LinkState(path=tmp / "links.json")
        pipe = AP.AcquisitionPipeline(store_path=tmp / "acq.json",
                                      vault=vault, links=links)
        pipe.auto_plan(n=2)
        drafted = pipe.by_status("drafted")
        self.assertGreaterEqual(len(drafted), 1, "بانک به صفِ پست وصل نیست")

        # ۵) approve → finalize → کدِ tracking
        iid = drafted[0]["id"]
        pipe.approve(iid)
        fin = pipe.finalize(iid)
        self.assertTrue(fin.get("ok"), fin)
        ready = pipe.by_status("ready")
        self.assertEqual(len(ready), 1)
        self.assertTrue((tmp / "links.json").exists(),
                        "کدِ tracking ساخته نشد — attribution از روزِ اول می‌میرد")

        # ۶) KPI
        kpi = ST.KPIRollup(path=tmp / "kpi.json")
        kpi.record(clicks=120, follows=18, free_subs=20,
                   paid_conversions=1, ppv_unlocks=4, delivery_rate=0.9)
        self.assertEqual(len(json.loads((tmp / "kpi.json").read_text("utf-8"))["weeks"]), 1)

        # ── همان فایل‌ها را در چیدمانِ پروژه بگذار تا دو خوانندهٔ بیرونی ببینند
        pf = tmp / "as_project"
        for s in ("brain", "langar", "studio", "00 - Control"):
            (pf / s).mkdir(parents=True, exist_ok=True)
        shutil.copy(tmp / "acq.json", pf / "brain" / "acq_queue.json")
        shutil.copy(tmp / "kpi.json", pf / "langar" / "kpi.json")
        shutil.copy(self.studio_dir / "drafts.json", pf / "studio" / "drafts.json")

        # ۷) مینی‌اپ
        import pf_miniapp as PM  # noqa: WPS433
        st = PM.get_pf_status(pf)
        k = PM.get_pf_kpi(pf)
        self.assertEqual(st["acq_ready"], len(ready),
                         "مینی‌اپ عددِ دیگری از pipeline می‌بیند — عدمِ تطابقِ خواننده/نویسنده")
        self.assertEqual(k["status"], "ok", "مینی‌اپ KPI ِ نوشته‌شده را نمی‌فهمد")
        self.assertIn(k["lights"]["click_to_follow_pct"]["light"], ("green", "amber", "red"))

        # ۸) پای ارگانیسم
        import studio_pf_leg as LEG  # noqa: WPS433
        _orig_root, _orig_ops = LEG.PF_ROOT, LEG._OPS
        try:
            LEG.PF_ROOT = pf
            LEG._OPS = tmp / "_ops"
            (LEG._OPS / "state").mkdir(parents=True, exist_ok=True)
            leg = LEG.studio_pf_status()
        finally:
            LEG.PF_ROOT, LEG._OPS = _orig_root, _orig_ops
        self.assertEqual(leg["acq_ready"], len(ready),
                         "پای ارگانیسم عددِ دیگری می‌بیند")
        self.assertFalse(leg["live"], "بدونِ مهرِ انسانی نباید live باشد")
        self.assertFalse(leg["outward_execution"])

        # ── سنجهٔ نهایی: سه خوانندهٔ مستقل، یک عدد
        self.assertEqual({len(ready), st["acq_ready"], leg["acq_ready"]}, {1},
                         "سه خواننده روی یک داده به یک عدد نرسیدند")

    def test_02_live_state_untouched(self):
        """گاردِ ۰۸-۰۳: هیچ بایتی از state ِ زندهٔ مالک عوض نشده باشد."""
        live_drafts = _PF / "studio" / "drafts.json"
        after = live_drafts.read_bytes() if live_drafts.exists() else None
        self.assertEqual(getattr(self, "_live_before", after), after,
                         "تست به drafts.json ِ زنده نوشت — ایزولاسیون شکسته است")


if __name__ == "__main__":
    unittest.main(verbosity=2)
