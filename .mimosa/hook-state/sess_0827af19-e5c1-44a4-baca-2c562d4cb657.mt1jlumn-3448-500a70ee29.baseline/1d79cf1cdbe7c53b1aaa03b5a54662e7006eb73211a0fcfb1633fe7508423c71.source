"""نقطهٔ ورودِ مغزِ کنترل.

حالت‌ها:
  python app.py                 → داشبورد وب + (اگر رمز تلگرام باشد) ربات. رمزِ KeePassXC یک‌بار پرسیده می‌شود.
  python app.py status          → وضعیت همه
  python app.py start demo      → روشن‌کردن (رمزهای پروژه تزریق می‌شوند)
  python app.py stop demo
  python app.py test demo
  python app.py halt | resume
  python app.py secrets-check    → بررسیِ اینکه همهٔ رمزهای موردنیاز در KeePassXC هستند (بدون نمایشِ مقدار)

محلِ نگه‌داریِ حالت با CONTROL_STATE_DIR قابل‌تغییر است (توصیه: بیرون از vault)."""
import os
import sys
from pathlib import Path

from core.manager import ProjectManager
from core.authz import Authz
from core.registry import Registry
from core.runner import ProcessRunner
from core.safety import SafetyGate
from core.store import Store

ROOT = Path(__file__).resolve().parent


def _load_env() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())


def _state_dir() -> Path:
    return Path(os.environ.get("CONTROL_STATE_DIR") or ROOT)


def _single_instance_lock():
    """قفل تک‌نمونه: سوکت انحصاری روی لوپ‌بک (پیش‌فرض 127.0.0.1:8768، env: BRAIN_LOCK_PORT).

    تا وقتی پروسه زنده است سوکت باز می‌ماند؛ kill/crash → آزادسازی خودکار.
    برگشتی: سوکت (باید تا پایان عمر پروسه نگه داشته شود) یا None اگر نمونهٔ دیگری قفل را دارد."""
    import socket
    port = int(os.environ.get("BRAIN_LOCK_PORT", "8768"))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):  # ویندوز — جلوی bind دوباره حتی با SO_REUSEADDR
        s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    try:
        s.bind(("127.0.0.1", port))
        s.listen(1)
        return s
    except OSError:
        s.close()
        return None


# نگاشت عنوان رمز → متغیر .env (پچ «مغز دوم» — fallback بدون KeePass)
ENV_SECRET_MAP = {
    "deepseek-key": "DEEPSEEK_API_KEY",
    "anthropic-key": "ANTHROPIC_API_KEY",  # حاوی کلید DeepSeek است (مسیریابی via ANTHROPIC_BASE_URL)
    "painting-telegram-token": "PAINTING_TELEGRAM_TOKEN",
    "tavily-key": "TAVILY_API_KEY",
    "accounting-telegram-token": "ACCOUNTING_TELEGRAM_TOKEN",
    "sakana-fugu-key": "SAKANA_API_KEY",
}


def _build_secrets():
    """KEEPASS_DB تنظیم باشد → KeePassXC؛ وگرنه fallback به .env (پچ مغز دوم)."""
    kdbx = os.environ.get("KEEPASS_DB", "").strip()
    if not kdbx:
        from core.secrets import DictSecrets
        m = {t: os.environ.get(k, "").strip()
             for t, k in ENV_SECRET_MAP.items() if os.environ.get(k, "").strip()}
        return DictSecrets(m) if m else None
    keyfile = os.environ.get("KEEPASS_KEYFILE", "").strip() or None
    pw = os.environ.get("KEEPASS_PASSWORD", "")
    if not pw:
        import getpass
        pw = getpass.getpass("🔐 رمزِ اصلیِ KeePassXC (یک‌بار): ")
    from core.secrets import KeePassSecrets
    try:
        return KeePassSecrets(kdbx, pw, keyfile)
    except Exception as e:  # noqa: BLE001
        print(f"❌ باز کردنِ فایلِ رمزها نشد: {e}")
        raise SystemExit(1)


def _build_authz(registry):
    users_yaml = ROOT / "config" / "users.yaml"
    owner = int(os.environ.get("OWNER_CHAT_ID") or registry.owner_chat_id or 0)
    if users_yaml.exists():
        az = Authz.from_yaml(users_yaml)
        if az.all_users():
            adm = az.admin()
            if adm and not adm.telegram_chat_id and owner:
                adm.telegram_chat_id = owner
            return az
    return Authz.seeded_admin(owner, "admin")


def build_context(secrets=None):
    state = _state_dir()
    registry = Registry(ROOT / "config" / "projects.yaml")
    store = Store(state / "data" / "state.db")
    safety = SafetyGate(store, state / "STOP")
    authz = _build_authz(registry)
    manager = ProjectManager(registry, store, safety, ProcessRunner(), secrets=secrets, authz=authz)
    return registry, store, safety, manager, authz


def _secrets_check(registry, secrets) -> None:
    if secrets is None:
        print("ℹ️ KEEPASS_DB تنظیم نشده — لایهٔ رمز غیرفعال است.")
        return
    missing = False
    for p in registry.all():
        for env_var, ref in (p.secrets or {}).items():
            ok = secrets.has(ref)
            missing = missing or (not ok)
            print(f"{'✅' if ok else '❌'} {p.id}: {env_var} ← «{ref}»")
    print("\nهمهٔ رمزها پیدا شد ✅" if not missing else "\nبعضی رمزها در KeePassXC نیستند ❌")


def cli(action: str, args) -> None:
    _load_env()
    need_secrets = action in ("start", "test", "secrets-check")
    secrets = _build_secrets() if need_secrets else None
    registry, store, safety, manager, authz = build_context(secrets=secrets)
    actor = authz.admin()
    if action == "status":
        if safety.is_halted():
            print("⛔ قفل ایمنی روشن است.")
        for s in manager.status_all(actor):
            print(f"- {s.name} [{s.state}] فعال={s.enabled} شناسه={s.pid or '-'} {s.detail}")
    elif action == "secrets-check":
        _secrets_check(registry, secrets)
    elif action in ("start", "stop", "test") and args:
        pid = args[0]
        if action == "test":
            ok, out = manager.test(pid, actor)
            print(("✅ سبز" if ok else "❌ قرمز") + f"\n{out}")
        else:
            r = getattr(manager, action)(pid, actor)
            print(f"{r.name}: {r.detail} [{r.state}]")
    elif action == "users":
        for u in authz.all_users():
            print(f"- {u.id}: {u.name} [{u.role.value}] chat={u.telegram_chat_id or '-'} فعال={u.enabled}")
    elif action == "halt":
        safety.halt("از خط فرمان"); print("⛔ متوقف شد.")
    elif action == "resume":
        safety.resume(); print("✅ ادامه.")
    else:
        print(__doc__)


def serve() -> None:
    _load_env()
    _lock = _single_instance_lock()   # noqa: F841 — عمداً نگه داشته می‌شود تا قفل آزاد نشود
    if _lock is None:
        dp = os.environ.get("DASHBOARD_PORT", "8770")
        print("⛔ یک نمونهٔ دیگر از مغز کنترل همین حالا روشن است — این نمونه اجرا نشد (ضد Conflict تلگرام).")
        print(f"   از همان نمونه استفاده کن: http://127.0.0.1:{dp}")
        print("   اگر پنجره‌ای نمی‌بینی، احتمالاً نمونهٔ مخفی autostart است؛ بستنش (PowerShell):")
        print("   Get-CimInstance Win32_Process | ? {$_.CommandLine -match 'app\\.py'} | % {Stop-Process -Id $_.ProcessId -Force}")
        raise SystemExit(1)
    secrets = _build_secrets()   # رمزِ KeePassXC یک‌بار همین‌جا پرسیده می‌شود
    registry, store, safety, manager, authz = build_context(secrets=secrets)
    from adapters.dashboard import start_dashboard

    port = int(os.environ.get("DASHBOARD_PORT", "8770"))
    start_dashboard(manager, safety, port=port)
    print(f"🌐 داشبورد: http://127.0.0.1:{port}")
    if secrets:
        print("🔐 لایهٔ رمزها فعال است (KeePassXC).")

    token = os.environ.get("TELEGRAM_TOKEN", "").strip()
    owner = int(os.environ.get("OWNER_CHAT_ID") or registry.owner_chat_id or 0)
    if token and owner:
        # --- مغز دوم v2: حافظه + دروازه + صف تأیید + کارت‌رسان (فاز ۲) ---
        from core.approval import ApprovalQueueDB, Notifier
        from core.channels import TelegramChannel, WhatsAppChannel
        from core.gateway import Gateway
        from core.memory import Memory

        memory = Memory(ROOT / "core.db")
        gateway = Gateway(memory)

        def _resolve_chat(to_ref: str):
            u = next((u for u in authz.all_users() if u.id == to_ref and u.enabled), None)
            return u.telegram_chat_id if (u and u.telegram_chat_id) else None

        tg_channel = TelegramChannel(token, _resolve_chat)
        queue = ApprovalQueueDB(memory, {"telegram": tg_channel, "whatsapp": WhatsAppChannel()})
        Notifier(memory, tg_channel, owner).start()
        print("🧠 لایهٔ v2 فعال: حافظه + دروازه + صف تأیید (approve-first).")

        from evolution.brain import EvolutionBrain
        evolution = EvolutionBrain(memory, gateway)

        from adapters import telegram_bot
        telegram_bot.set_token(token)
        app = telegram_bot.build_application(manager, safety, owner,
                                             memory=memory, queue=queue, gateway=gateway,
                                             evolution=evolution)
        print("🤖 ربات تلگرام روشن شد. در تلگرام /status بزن. (/queue و /briefs هم هست)")
        app.run_polling()
    else:
        print("ℹ️ رمز تلگرام یا آی‌دی مالک تنظیم نشده — فقط داشبورد بالاست. (Ctrl+C برای خروج)")
        import time
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            print("خداحافظ.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cli(sys.argv[1], sys.argv[2:])
    else:
        serve()
