"""قفلِ ایمنیِ سراسری (دکمهٔ توقف اضطراری): فایلِ STOP + پرچمِ پایگاه‌داده، هر دو با هم."""
from pathlib import Path


class SafetyGate:
    def __init__(self, store, stop_file):
        self.store = store
        self.stop_file = Path(stop_file)

    def is_halted(self) -> bool:
        return self.stop_file.exists() or self.store.get_flag("halted") == "1"

    def halt(self, reason: str = "") -> None:
        self.stop_file.write_text(reason or "halted", encoding="utf-8")
        self.store.set_flag("halted", "1")
        self.store.log("halt", "-", reason)

    def resume(self) -> None:
        if self.stop_file.exists():
            self.stop_file.unlink()
        self.store.set_flag("halted", "0")
        self.store.log("resume", "-", "")
