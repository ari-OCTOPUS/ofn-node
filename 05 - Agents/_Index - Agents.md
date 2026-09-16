---
type: moc
status: active
tags: [agents, ai, automation]
updated: 2026-07-04
---

# ایندکس Agents

> شناسنامه هر ایجنت/ربات فعال در اکوسیستم — چه می‌کند، کجا مستقر است، چطور کنترل می‌شود.

## فعال (Research Scout Fleet — از 2026-07-04)

- [[05 - Agents/Research Scout Fleet|Research Scout Fleet]] — ناوگان ۸ اسکات زمان‌بندی روزانه (تحقیق عمیق هر پروژه → `00 - Inbox/scout-digests/`).
- [[05 - Agents/Mycelium Scout|Mycelium Scout]] — طراحی زیست‌الگو (میسیلیوم/قارچ) + اسکات طبیعت/architect.
- [[05 - Agents/Vault Cartographer|Vault Cartographer]] — نقشه‌بردارِ معماری (read-only floor / propose-only ceiling)؛ پایِ OLP-1: [[05 - Agents/Vault-Cartographer-LIMB|limb conformance]].
- رجیستری و autonomy: [[05 - Agents/AGENT_REGISTRY|AGENT_REGISTRY]].

## قالب پیشنهادی (هر ایجنت یک نوت)

```
type: agent
name / نقش / پروژه میزبان
مستقر در: (VPS / Orange Pi / لوکال)
کانال کنترل: (تلگرام / CLI)
وضعیت: active | paused
لینک کد و runbook
```

## کاندیداهای اولیه

- ربات کنترل تلگرام architect — [[04 - Architect System/architect/PROJECT|architect]]
- ایجنت‌های brushline (researcher، content، lead_capture و…) — [[03 - Projects/Lead-نقاشی/PROJECT|Lead-نقاشی]]
- ربات‌های Mining (sentinel، QuantumAlphaBot) — [[03 - Projects/Mining/PROJECT|Mining]]

## نوت‌های مرتبط

- [[01 - Dashboard/Home|Home]]
