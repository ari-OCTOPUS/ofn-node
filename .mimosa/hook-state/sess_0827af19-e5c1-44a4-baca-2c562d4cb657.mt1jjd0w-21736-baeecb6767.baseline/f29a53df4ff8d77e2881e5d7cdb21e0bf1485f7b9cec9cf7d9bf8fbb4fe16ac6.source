"""test_tg_metadata_scan.py — نقشه‌برداریِ metadata (telegram_center/metadata_scan.py).

پوشش: scan روی temp dir فقط metadata می‌گیرد (size/mtime/ext)، محتوا را echo نمی‌کند،
manifest/state/audit نوشته می‌شوند، excludeها رعایت می‌شوند، max_files/seconds truncation
کار می‌کند، و .env هرگز hash نمی‌شود. صفر شبکه، صفر نوشتنِ خارج از temp harness.
"""
import io
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness  # noqa: E402
ENV = harness.setup("tg-metadata-scan")

# مسیرهای خروجی metadata_scan را به یک sandboxِ temp هدایت کنیم تا state واقعی
# انتخاب نشود. ماژول از _OCTOPUS استفاده می‌کند؛ آن را override می‌کنیم.
sys.path.insert(0, str(_HERE.parent / "telegram_center"))
import metadata_scan as ms   # noqa: E402

# sandbox در سطحِ ماژول نیست — هر تست با setup_paths()/tempfile.mkdtemp خودش
# یک sandbox تازه می‌سازد تا بین تست‌ها تداخل نباشد.


def setup_paths():
    """جابه‌جاییِ مسیرهای خروجی ماژول به sandboxِ تازه per-test (هیچ ردی روی F:\\backup،
    هیچ تداخلِ بین تست‌ها). هر تست sandbox/درختِ نوی خودش را می‌سازد."""
    sb = Path(tempfile.mkdtemp(prefix="octopus-mscan-"))
    oct = sb / "_octopus"
    ms._OCTOPUS = oct
    ms._MANIFEST_DIR = oct / "manifests"
    ms._HISTORY_DIR = ms._MANIFEST_DIR / "history"
    ms._REPORTS_DIR = oct / "reports" / "daily"
    ms._STATE_PATH = oct / "state" / "metadata_scan.json"
    ms._AUDIT_PATH = oct / "logs" / "audit.log"
    return sb


def _make_tree():
    """ساختِ یک درختِ کوچک و معنادار برای scan (در یک sandboxِ تازه)."""
    sb = setup_paths()
    root = sb / "fakewroot"
    (root / "docs").mkdir(parents=True)
    (root / "src").mkdir(parents=True)
    (root / "src" / "__pycache__").mkdir(parents=True)      # باید exclude شود
    (root / "node_modules").mkdir(parents=True)             # باید exclude شود
    (root / "docs" / "readme.md").write_text("# hi", "utf-8")
    (root / "src" / "a.py").write_text("print('a' * 100)", "utf-8")
    (root / "src" / "b.py").write_text("x = 1", "utf-8")
    (root / "src" / "__pycache__" / "a.cpython-310.pyc").write_bytes(b"\x00" * 50)
    (root / "node_modules" / "lib.js").write_text("module.exports={}", "utf-8")
    (root / ".env").write_text("SECRET=do_not_read_me_xyz", "utf-8")  # bait — نباید hash شود
    (root / "data.json").write_text('{"k": 1}', "utf-8")
    return root


# ─── تست‌ها ──────────────────────────────────────────────────────────────────────
def t_a_scan_returns_manifest_with_metadata_only():
    setup_paths()
    root = _make_tree()
    r = ms.scan_metadata(root)
    assert isinstance(r, dict)
    paths = [f["path"] for f in r["files"]]
    assert "docs/readme.md" in paths
    assert "src/a.py" in paths
    assert "data.json" in paths
    # هر فایل فقط metadata دارد — نه محتوا
    for f in r["files"]:
        assert set(f.keys()) <= {"path", "type", "size", "mtime", "ext", "sha256_64k"}
        assert "content" not in f


def t_b_excludes_are_skipped():
    setup_paths()
    root = _make_tree()
    r = ms.scan_metadata(root)
    paths = [f["path"] for f in r["files"]]
    assert not any("node_modules" in p for p in paths), "node_modules باید exclude شود"
    assert not any("__pycache__" in p for p in paths), "__pycache__ باید exclude شود"


def t_c_env_secret_never_hashed_even_with_flag():
    """حتی با OCTOPUS_METADATA_HASH=1 فایلِ .env نباید hash بخورد (gating)."""
    setup_paths()
    root = _make_tree()
    os.environ[ms.HASH_FLAG] = "1"
    try:
        r = ms.scan_metadata(root, hash_files=True)
    finally:
        os.environ.pop(ms.HASH_FLAG, None)
    env_entry = next((f for f in r["files"] if f["path"] == ".env"), None)
    assert env_entry is not None, ".env باید به‌عنوان metadata وجود داشته باشد"
    assert "sha256_64k" not in env_entry, ".env نباید hash شود"
    # ولی فایل‌های دیگر با فلگ hash می‌شوند
    hashed = [f for f in r["files"] if "sha256_64k" in f]
    assert len(hashed) >= 1, "با فلگ، حداقل یک فایل باید hash شود"


def t_d_max_files_truncates():
    setup_paths()
    root = _make_tree()
    r = ms.scan_metadata(root, max_files=2)
    assert r["truncated"] is True
    assert r["summary"]["files"] == 2


def t_e_state_written_running_then_done():
    setup_paths()
    root = _make_tree()
    ms.scan_metadata(root)
    st = ms.load_state()
    assert st["status"] == "done"
    assert st["files_seen"] > 0
    assert isinstance(st["finished_at"], str)


def t_f_write_manifest_creates_latest_history_report():
    setup_paths()
    root = _make_tree()
    r = ms.scan_metadata(root)
    paths = ms.write_manifest(r)
    assert paths["latest"] and Path(paths["latest"]).exists()
    assert paths["history"] and Path(paths["history"]).exists()
    assert paths["report"] and Path(paths["report"]).exists()
    # latest معتبر JSON است
    loaded = json.loads(Path(paths["latest"]).read_text("utf-8"))
    assert loaded["summary"]["files"] == r["summary"]["files"]


def t_g_audit_appended_content_free():
    setup_paths()
    root = _make_tree()
    r = ms.scan_metadata(root)
    ms.write_manifest(r)
    audit_txt = ms._AUDIT_PATH.read_text("utf-8")
    assert "metadata_scan" in audit_txt
    # bait نباید در audit نشت کند
    assert "do_not_read_me_xyz" not in audit_txt


def t_h_summarize_manifest_human_readable():
    setup_paths()
    root = _make_tree()
    r = ms.scan_metadata(root)
    s = ms.summarize_manifest(r)
    assert "فایل" in s and "پوشه" in s
    assert ms.summarize_manifest({}).startswith("🐙") or "هنوز" in ms.summarize_manifest({})
    assert ms.summarize_manifest(None).startswith("🐙")


def t_i_broken_input_safe():
    """وجود نداشتنِ ریشه یا pathِ خراب → crash نمی‌کند."""
    setup_paths()
    r = ms.scan_metadata(Path(tempfile.gettempdir()) / "does_not_exist_xyz_octopus_test")
    assert isinstance(r, dict)
    # خطاها شمرده شده، scan تمام شده
    assert r["summary"]["files"] == 0


def t_j_human_bytes_format():
    assert ms._human_bytes(0) == "0 B"
    assert "KiB" in ms._human_bytes(2048)
    assert "MiB" in ms._human_bytes(5 * 1024 * 1024)


def t_k_load_state_default_when_missing():
    setup_paths()
    # state وجود ندارد (sandbox تازه)
    if ms._STATE_PATH.exists():
        ms._STATE_PATH.unlink()
    st = ms.load_state()
    assert st["status"] == "idle" and st["files_seen"] == 0


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_metadata_scan: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
