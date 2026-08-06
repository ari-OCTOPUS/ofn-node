"""test_tg_approval_store.py — پلِ صفِ تأیید (telegram_center/approval_store.py).

پوشش: add/approve/reject/mark_done در approvals.json اختاپوس، sanitize id، bridge با
مسیرِ قدیمی، fail-soft روی ورودیِ خراب. صفر شبکه، صفر نوشتنِ خارج از sandbox.
"""
import json
import shutil
import sys
import tempfile
import threading
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness  # noqa: E402
ENV = harness.setup("tg-approval-store")

sys.path.insert(0, str(_HERE.parent / "telegram_center"))
import approval_store as aps   # noqa: E402

def setup_paths():
    """هدایتِ مسیرهای ماژول به sandboxِ تازه per-test (هیچ ردی روی F:\\backup،
    هیچ تداخلِ بین تست‌ها)."""
    sb = Path(tempfile.mkdtemp(prefix="octopus-apstore-"))
    oct_state = sb / "_octopus" / "state"
    aps._OCTOPUS_STATE = oct_state
    aps._APPROVALS_JSON = oct_state / "approvals.json"
    aps._AUDIT_PATH = sb / "_octopus" / "logs" / "audit.log"
    aps._LEGACY_DIR = sb / "_ops" / "state" / "telegram" / "approvals"
    aps._ROOT = sb
    return sb


# ─── تست‌ها ──────────────────────────────────────────────────────────────────────
def t_a_add_pending_creates_job_with_id():
    setup_paths()
    jid = aps.add_pending({"type": "metadata_scan", "title": "نقشه‌برداری", "risk": "read"})
    assert jid and jid.startswith("job_")
    pending = aps.load_pending()
    assert len(pending) == 1
    assert pending[0]["id"] == jid
    assert pending[0]["status"] == "pending"
    assert pending[0]["risk"] == "read"


def t_b_add_duplicate_id_idempotent():
    setup_paths()
    jid = aps.add_pending({"type": "move_files", "id": "fixed-id", "title": "x"})
    jid2 = aps.add_pending({"type": "move_files", "id": "fixed-id", "title": "y"})
    # id صریحِ کاربر حفظ می‌شود (قرارداد: احترام به id داده‌شده)
    assert jid == jid2 == "fixed-id"
    assert len(aps.load_pending()) == 1, "id تکراری نباید دوباره اضافه شود"


def t_c_approve_moves_pending_to_approved():
    setup_paths()
    jid = aps.add_pending({"type": "budget_apply", "title": "بودجه", "risk": "high"})
    assert aps.approve(jid) is True
    assert len(aps.load_pending()) == 0
    s = aps.summary()
    assert s["approved"] == 1 and s["pending"] == 0


def t_d_reject_moves_pending_to_rejected():
    setup_paths()
    jid = aps.add_pending({"type": "x", "title": "y"})
    assert aps.reject(jid) is True
    s = aps.summary()
    assert s["rejected"] == 1 and s["pending"] == 0


def t_e_mark_done_after_approve():
    setup_paths()
    jid = aps.add_pending({"type": "x", "title": "y"})
    aps.approve(jid)
    assert aps.mark_done(jid) is True
    assert aps.summary()["done"] == 1


def t_f_approve_unknown_id_returns_false():
    setup_paths()
    aps.add_pending({"type": "x", "title": "y"})
    assert aps.approve("does-not-exist") is False
    assert aps.approve("") is False


def t_g_sanitize_id_blocks_path_traversal():
    setup_paths()
    # تلاشِ تزریق path — sanitize باید کاراکترهای خطرناک را حذف کند
    jid = aps.add_pending({"type": "x", "id": "../../etc/passwd", "title": "y"})
    assert ".." not in jid and "/" not in jid and "\\" not in jid
    # id ساخته‌شده امن است و در نامِ فایلِ legacy هم نمی‌تواند فرار کند:
    aps.record_legacy_verdict(jid, "ok")
    # هیچ فایلی خارج از legacy dir ساخته نشده
    for p in (aps._LEGACY_DIR.rglob("*")):
        assert p.resolve().is_relative_to(aps._LEGACY_DIR.resolve())


def t_h_summary_returns_all_buckets():
    setup_paths()
    s = aps.summary()
    assert set(s.keys()) == {"pending", "approved", "rejected", "done"}
    assert all(isinstance(v, int) for v in s.values())


def t_i_get_finds_job_in_any_bucket():
    setup_paths()
    jid = aps.add_pending({"type": "x", "title": "y"})
    aps.approve(jid)
    job = aps.get(jid)
    assert job is not None
    assert job["status"] == "approved"
    assert aps.get("missing") is None


def t_j_legacy_bridge_sync_reads_old_verdicts():
    setup_paths()
    # ساختِ چند verdict قدیمی
    aps._LEGACY_DIR.mkdir(parents=True, exist_ok=True)
    (aps._LEGACY_DIR / "abc.json").write_text(
        json.dumps({"id": "abc", "verdict": "ok", "ts": "2026-07-01"}), "utf-8")
    (aps._LEGACY_DIR / "def.json").write_text(
        json.dumps({"id": "def", "verdict": "no", "ts": "2026-07-02"}), "utf-8")
    sync = aps.sync_to_octopus_state()
    assert sync["count"] == 2
    assert len(sync["recent"]) == 2


def t_k_legacy_bridge_writes_verdict():
    setup_paths()
    assert aps.record_legacy_verdict("job-123", "ok") is True
    p = aps._LEGACY_DIR / "job-123.json"
    assert p.exists()
    rec = json.loads(p.read_text("utf-8"))
    assert rec["verdict"] == "ok" and rec["id"] == "job-123"
    # jsonl هم append شده
    assert (aps._LEGACY_DIR / "approvals.jsonl").exists()


def t_l_load_octopus_approvals_empty_when_missing():
    setup_paths()
    # approvals.json هنوز نیست
    if aps._APPROVALS_JSON.exists():
        aps._APPROVALS_JSON.unlink()
    state = aps._load_octopus_approvals()
    assert state["pending"] == [] and state["schema_version"] == 1


def t_m_broken_input_does_not_crash():
    setup_paths()
    assert aps.add_pending(None) == ""                  # type: ignore[arg-type]
    assert aps.add_pending({}) != ""                    # خالی → id تولید می‌شود
    assert aps.get(None) is None                        # type: ignore[arg-type]
    assert isinstance(aps.summary(), dict)


def t_n_content_not_stored_in_job():
    """محتوای کاربر هرگز در job ذخیره نمی‌شود — فقط title/type/risk."""
    setup_paths()
    jid = aps.add_pending({"type": "scan", "title": "x",
                           "sensitive_content": "secret-xyz-bait"})
    pending = aps.load_pending()
    job = pending[0]
    assert "sensitive_content" not in job          # content-free invariant HOLDS
    # 2026-07-22 characterization migration: `expires_epoch` (callback-token TTL,
    # added 2026-07-20 Stage-1, approval_store.py:151) is legitimate CONTENT-FREE
    # metadata (an int timestamp), so it is added to the allowed key set. The
    # privacy invariant (no user content) is unchanged — only the stale whitelist
    # is brought up to the current contract.
    assert set(job.keys()) <= {"id", "type", "title", "status", "risk", "created_at",
                               "expires_epoch", "requires_confirmation",
                               "dry_run_report", "source"}


def t_o_cross_process_lock_serializes_dual_writer_race():
    """VQ-APPROVAL-DUALWRITE-001 (۲۰۲۶-۰۸-۰۶): یک نویسندهٔ دومِ importlib-loaded
    — دقیقاً همان شکلی که goal_action_bridge._load_approval_store() از پروسهٔ
    organism.py ماژول را لود می‌کند — نباید approve ِ هم‌زمانِ نویسندهٔ اول
    (center، همین ماژول `aps`) را overwrite کند.

    قبل از فیکس: RLock ِ approval_store فقط درون‌پروسه بود؛ نویسندهٔ دوم
    load→(تأخیر)→save می‌کرد و snapshotِ کهنه (بدونِ approve) را می‌نوشت —
    تصمیمِ مالک بی‌صدا پاک می‌شد. بعد از فیکس: opslib.LockedJson دو نویسنده
    را — حتی از دو ماژول/شیِ RLock ِ متفاوت — روی همان approvals.json
    serialize می‌کند."""
    setup_paths()
    jid = aps.add_pending({"type": "debate", "title": "owner-idea", "risk": "medium"})

    # aps2 = ماژولِ دومِ importlib-loaded (goal_action_bridge._load_approval_store
    # هم دقیقاً همین را می‌کند)، با _STORE_LOCK ِ RLock ِ خودش — کاملاً بی‌ربط به
    # RLock ِ aps. تنها چیزِ مشترک، مسیرِ approvals.json روی دیسک است.
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_race_approval_store", str(Path(aps.__file__)))
    aps2 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(aps2)
    for attr in ("_APPROVALS_JSON", "_AUDIT_PATH", "_LEGACY_DIR", "_ROOT"):
        setattr(aps2, attr, getattr(aps, attr))

    # پنجرهٔ شکست را عمداً باز نگه می‌داریم: aps2 بعد از خواندنِ snapshot (زیرِ
    # قفلِ فایل، چون فیکس load را داخلِ `with opslib.LockedJson(...)` برده) کمی
    # صبر می‌کند — دقیقاً همان بازهٔ T0..T1 ِ گزارش‌شده.
    orig_load = aps2._load_octopus_approvals
    def _slow_load():
        state = orig_load()
        time.sleep(0.4)
        return state
    aps2._load_octopus_approvals = _slow_load

    result: dict = {}
    def _organism_writer():
        result["jid2"] = aps2.add_pending({"type": "mission_approval", "title": "z"})
    th = threading.Thread(target=_organism_writer)
    th.start()
    time.sleep(0.1)   # مطمئن شو aps2 اول قفلِ فایل را گرفته و داخلِ تأخیر است

    t0 = time.time()
    assert aps.approve(jid) is True, "approve نباید به‌خاطرِ نویسندهٔ دوم شکست بخورد"
    waited = time.time() - t0
    th.join(timeout=5)
    assert not th.is_alive(), "نویسندهٔ دوم (organism-شبیه‌سازی‌شده) تمام نشد"

    # اثباتِ mutual exclusion: approve واقعاً منتظرِ آزادشدنِ قفلِ فایل ماند —
    # اگر قفل بی‌اثر بود، approve بلافاصله (بدونِ صبر) برمی‌گشت.
    assert waited >= 0.2, f"approve بدونِ صبر برای قفلِ نویسندهٔ دوم رد شد ({waited:.3f}s)"

    final = aps.summary()
    assert final["approved"] == 1, f"approveِ مالک زیرِ نویسندهٔ دوم گم شد: {final}"
    assert aps.get(jid)["status"] == "approved"
    assert aps.get(result["jid2"]) is not None, "نوشتنِ نویسندهٔ دوم هم باید بماند (هیچ‌کدام گم نشود)"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_approval_store: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
