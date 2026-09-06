# OWNER-SIGN-PACK (گزینهٔ B)

هدف: پاکت‌های OWNER-GO با امضای Ed25519 خود مالک رسماً معتبر شوند تا
`T-04` (authority single-valued) و `T-11` (ingress rejects unsigned) از صفر خارج شوند
و تناقض گزارش دور ۳۹ (UNLOCK restored vs NOT_AUTHENTICATED) با احراز هویت واقعی حل شود.

## اجرا (فقط خود مالک — هیچ ایجنتی این را اجرا نمیکند)

```bash
cd ~/.octopus-signing  exists?  ls
bash "F:/backup/06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/OWNER-SIGN-PACK/sign-owner-go.sh" \
  PACKET1.json PACKET2.json
```

- کلید: `~/.octopus-signing/octopus-owner-ed25519-private.pem` (روی همین لپتاپ هست؛ اسکریپت فقط امضا میکند، کلید را چاپ/کپی/جابه‌جا نمیکند)
- خروجی: `<packet>.sig` (base64) + `OWNER-SIGN-MANIFEST.jsonl` (file, sha256, sig, key_fp16, scheme)
- بعدش: با تأیید مالک، `.sig`ها + manifest به ۱۳۸ منتقل و verifier سمت برد فعال میشود (transport با رسید)

## چه پاکت‌هایی امضا شود (پیشنهاد — مالک تایید نهایی)

UNLOCK-L1، UNLOCK-L2، ARM-ALL-ALLOWED، CHECKOUT1-AUTONOMOUS، SHELF1-AUTONOMOUS،
PAINTING-RANK-DRAFT، FIX-SLEEP-CAUSES (۷ پاکت فعالِ امروز؛ بقیهٔ ۱۰ ردیف registry در صورت نیاز).

## پس از امضا

- رأی D (ACCEPT_L2) لازم نمیماند؛ L2 با پاکت امضاشده و verifier رسماً باز میشود.
- MATURE قفلِ «زیر ۳۵٪» هم آزاد میشود چون ingress unsigned-reject قابل تست میگردد.
