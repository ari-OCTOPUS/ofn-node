# TODO — Mining Pre-Execution MVP

## فوری

- [ ] secrets موجود در کدهای قدیمی QuantumAlphaBot/config.py rotate و redact شوند.
- [ ] Hardware Registry واقعی پر شود.
- [ ] VERDICT_QUEUE با human answers بسته شود.
- [ ] برق واقعی هر محل ثبت شود.
- [ ] وضعیت فعلی mining فعال/غیرفعال تأیید شود.

## کد

- [ ] افزودن parser برای فایل Markdown رجیستری فعلی.
- [ ] افزودن schema validation سخت‌گیرانه‌تر.
- [ ] افزودن `confidence` به CoinCandidate score.
- [ ] افزودن tests برای CLI.
- [ ] افزودن report templates برای Obsidian frontmatter.

## طراحی

- [ ] تعریف schema رسمی `experiment_proposal.yaml`.
- [ ] تعریف schema رسمی `weekly_death_watch.yaml`.
- [ ] تعریف schema رسمی `benchmark_result.yaml`.
- [ ] طراحی read-only FleetHealth adapter.

## ممنوع تا verdict

- [ ] اجرای miner.
- [ ] SSH به نود.
- [ ] deploy.
- [ ] هر wallet access.
- [ ] هر buy/sell/withdraw.
