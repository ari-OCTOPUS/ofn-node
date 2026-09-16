# 🔒 Project-F RUNBOOK — اجرای امن و contained

> بیرون از پوشه فقط alias `Project-F`. هیچ محتوا/هویت/پلتفرم در گزارش‌های cross-project.

---

## اصول سخت

- consent و GATE 0 مقدم بر هر outward action.
- هیچ publish/DM/content generation/live action بدون verdict.
- cross-domain فقط state ژنریک: active/blocked/research/draft.
- Accounting فقط safe alias + سهم/کد غیرحساس را می‌بیند.
- body/identity/media/content بیرون از local containment echo نمی‌شود.

---

## Graph search قبل از کار

1. Load local `PROJECT.md`, `PROJECT-F-CONTROL-MANIFEST.json`, `OpenQuestions.md`, `DecisionLog.md`.
2. Outside folder, map node to `ProjectF` alias only.
3. Check `RISK-LADDER.md`: contained propose-only.
4. Any outward action → verdict request, stop.

---

## مجاز

- status-only report
- research/drafts inside containment
- consent/gate checklist
- local runbook/test notes
- Accounting safe alias touchpoint

## ممنوع

- identity/platform/content echo in root graph
- publish/send/spend
- explicit content processing in shared memory
- bypassing GATE 0

---

## Safe status schema

```yaml
project: Project-F
phase:
gate0: resolved/unresolved/unknown
branch: A/B/unknown
outward_actions_allowed: false
notes: content-free
```
