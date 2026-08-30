"""بارگذاری پیکربندی زیمان از ziman.yaml.

تنها منبعِ حقیقتِ اعداد و قواعد است؛ کد هیچ عددی را hard-code نمی‌کند.
"""
from pathlib import Path
from typing import Any, Dict


def load_config(path) -> Dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8")
    try:
        import yaml
    except ImportError as e:  # noqa: BLE001
        raise RuntimeError("PyYAML لازم است:  pip install PyYAML") from e
    cfg = yaml.safe_load(text) or {}
    # اعتبارسنجیِ حداقلی — زود شکست بخور اگر پیکربندی ناقص است
    for key in ("business", "capacity", "generation"):
        if key not in cfg:
            raise ValueError(f"ziman.yaml ناقص است: بخشِ «{key}» نیست.")
    if int(cfg["capacity"].get("units_per_week_ceiling", 0)) < 0:
        raise ValueError("units_per_week_ceiling نمی‌تواند منفی باشد.")
    return cfg
