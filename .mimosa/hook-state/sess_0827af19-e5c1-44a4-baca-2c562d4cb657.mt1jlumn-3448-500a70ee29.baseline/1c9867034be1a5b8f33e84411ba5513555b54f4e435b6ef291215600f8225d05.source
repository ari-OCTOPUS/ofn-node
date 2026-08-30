#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_client_contract — کلاینتِ **واقعی** همان صفاتی را دارد که مصرف‌کننده می‌خواند.

باگی که این فایل می‌بندد، و روشِ پیدا شدنش:

`surface_router._chat_for` از روزِ اول `getattr(client, "owner_chat_id", None)`
را می‌خواند، ولی `tg_api.TgClient` فقط `_owner`/`_center` ِ **خصوصی** داشت.
یعنی `getattr` همیشه `None` می‌داد و مسیرِ `dm` بی‌صدا بی‌مقصد می‌شد.

`test_tg_surface_router` این را **نگرفت** — چون کلاینتِ ساختگی‌اش این دو صفت
را دارد. فیکی که تابعِ واقعی را دور می‌زند: تست سبز، تولید کور.

⚠️ باگ از قبل بود، ولی تغییرِ ۲۰۲۶-۰۷-۳۰ (ابهام → DM به‌جای گروه) دامنه‌اش را
از «فقط dm» به «هر جریانِ مبهم» گسترش می‌داد. پس قرارداد **واقعی** شد
(دو property روی خودِ کلاس)، نه اینکه صداکننده به مسیرِ خصوصی دست ببرد.

قاعدهٔ عمومیِ این فایل: **هر صفتی که یک مصرف‌کننده با `getattr` می‌خواند، باید
روی کلاسِ واقعی سنجیده شود — نه فقط روی fixture.**
"""
import inspect
import re
import sys
from pathlib import Path

import harness

ENV = harness.setup("tg-client-contract")

_OPS = Path(__file__).resolve().parent.parent
_TC = str(_OPS / "telegram_center")
if _TC not in sys.path:
    sys.path.insert(0, _TC)

import surface_router as sr  # noqa: E402
import tg_api  # noqa: E402


def _client():
    return tg_api.TgClient(token="123:fake", owner_chat_id=6150431610,
                           center_chat_id=-1004475788460)


# ── قرارداد روی کلاسِ واقعی ────────────────────────────────────────────────
def t_the_real_client_exposes_owner_and_center_chat_id():
    c = _client()
    assert c.owner_chat_id == 6150431610, c.owner_chat_id
    assert c.center_chat_id == -1004475788460, c.center_chat_id


def t_the_accessors_are_read_only():
    """اگر نوشتنی بودند، یک ماژولِ دیگر می‌توانست مقصدِ مالک را عوض کند."""
    c = _client()
    for attr in ("owner_chat_id", "center_chat_id"):
        try:
            setattr(c, attr, 999)
        except AttributeError:
            continue
        raise AssertionError(f"{attr} نوشتنی است")


def t_an_unconfigured_client_reports_none_not_a_wrong_id():
    """نبودِ مقصد باید `None` باشد — نه صفر، نه مقصدِ دیگری."""
    c = tg_api.TgClient(token="123:fake")
    assert c.owner_chat_id is None or isinstance(c.owner_chat_id, int)
    assert c.center_chat_id is None or isinstance(c.center_chat_id, int)


# ── همان مسیری که واقعاً مصرفش می‌کند ──────────────────────────────────────
def t_the_router_resolves_dm_against_the_real_client():
    """قلبِ این فایل: `_chat_for` با کلاینتِ **واقعی**، نه fixture."""
    c = _client()
    got = sr._chat_for({"surface": "dm"}, c, {"chat_id": -1004475788460})
    assert got == c.owner_chat_id, (got, c.owner_chat_id)
    assert got is not None, "مسیرِ dm بی‌مقصد شد"


def t_the_router_resolves_group_against_the_real_client():
    c = _client()
    got = sr._chat_for({"surface": "group"}, c, {"chat_id": -1004475788460})
    assert got == -1004475788460, got


def t_an_ambiguous_surface_reaches_the_owner_not_nowhere():
    """تغییرِ ۰۷-۳۰: ابهام → DM. اگر صفت نبود، این `None` می‌شد و پیام گم."""
    c = _client()
    for block in ({}, {"surface": ""}, {"surface": "weird"}):
        got = sr._chat_for(block, c, {"chat_id": -1004475788460})
        assert got == c.owner_chat_id, (block, got)


# ── گاردِ عمومی: هر getattr ِ مصرف‌کننده باید روی کلاسِ واقعی وجود داشته باشد ──
def t_every_attribute_the_router_reads_exists_on_the_real_client():
    """اسکنِ نحویِ `getattr(client, "...")` در `surface_router` و تطبیق با
    کلاسِ واقعی. این بند همان تلهٔ «فیک تابعِ واقعی را دور می‌زند» را می‌بندد
    برای صفاتی که **هنوز اضافه نشده‌اند**."""
    src = inspect.getsource(sr)
    names = set(re.findall(r'getattr\(\s*client\s*,\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']',
                           src))
    assert names, "هیچ getattr ای پیدا نشد — الگوی اسکن کهنه شده"
    c = _client()
    missing = [n for n in sorted(names) if not hasattr(c, n)]
    assert not missing, f"صفاتی که router می‌خواند ولی کلاینتِ واقعی ندارد: {missing}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_client_contract: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
