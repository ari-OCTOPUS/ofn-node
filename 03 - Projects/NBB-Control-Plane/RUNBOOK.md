# 🧠 NBB-CP RUNBOOK — brain/control-plane

> وضعیت: built/hardened, but role relative to Architect/_ops is open.

---

## اصول سخت

- 12 invariants sacred؛ هیچ agent آن‌ها را تغییر نمی‌دهد.
- NBB-CP تا verdict نقش، فقط shadow/control-plane analysis.
- هیچ اتصال live به tenantها بدون verdict.
- no self-modification of invariants/gates/policy weights.

---

## Graph search قبل از کار

1. Load `app/MANIFEST.yaml`, `README.md`, `pyproject.toml` if needed.
2. Follow `NBB_CP → ArchitectOps ROLE_OPEN`.
3. Check root `VERDICT_QUEUE.md` VQ-ROOT-001 / VQ-NBB-001.
4. If task asks to govern projects live → verdict request.

---

## مجاز

- read-only audit
- adapter plan
- invariant mapping to tenants
- dashboard/read-only proposal

## ممنوع

- replacing Architect/_ops
- live enforcement
- policy rewrite
- executing code against tenant data without verdict

---

## Recommended first integration

```text
NBB-CP = portable sibling/adapter first, not replacement.
```
