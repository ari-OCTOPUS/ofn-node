# TRUST-ANCHOR — لنگر اعتماد کلید امضای مالک OCTOPUS

> دستور مالک #۷ §۲ (T41) — 2026-08-20.
> این فایل مرجع fail-closed همهٔ اسکریپت‌های امضا/verify است: پیش از هر verify،
> انگشت‌نگارتی DER کلید عمومی PEM باید دقیقاً با مقدار زیر تطبیق داده شود؛
> هر اختلاف = توقف (fail-closed)، حتی اگر خود verify سبز بدهد.
> مالک همین مقدار را جدا از مخزن (آفلاین) نگه می‌دارد.

```text
algorithm : Ed25519 (pure, openssl pkeyutl -rawin)
pubkey_pem: _ops/owner-signing/octopus-owner-ed25519-public.pem
der_fingerprint_sha256:
  2413e9746f13afc900b31ad4d966a6783d73662f661fa0d6dc578e9b244ab6b2
```

## روش محاسبه (تکرارپذیر)

```bash
openssl pkey -pubin -in _ops/owner-signing/octopus-owner-ed25519-public.pem \
  -outform DER | sha256sum
```

## سابقه

- 2026-08-20: تعیین لنگر پس از T34 ‏`KEY_IDENTITY_CONFIRMED_SAME`
  (PEM عمومی repo و `~/.octopus-signing` بایت‌به‌بایت یکسان؛ وریفای مستقل B1
  سبز). شاهد: `06-EVIDENCE/T34-KEY-IDENTITY-2026-08-20.md`.
