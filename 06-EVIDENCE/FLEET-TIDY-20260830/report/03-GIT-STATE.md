# 03 — وضعیت گیت همهٔ نودها (2026-08-30)

## برد ۱۳۸ — /home/ari/ofn (origin = ari-OCTOPUS/ofn-node)
| شاخه | SHA | نسبت با گیت‌هاب |
|---|---|---|
| work/truth-record-20260830 (HEAD) | 9bc05abc | یکسان ✓ |
| backup/board138-20260830 | c1969bce | یکسان ✓ (immutable) |
| integration/138-business-spine-20260828 | a27eb053 | **این اجرا FF شد** (6881337→a27eb053) |
| بقیهٔ ۸ شاخه (audit/*, discovery/*, octopus/*, ofn-*) | — | همگی یکسان با گیت‌هاب ✓ |
| main (محلی برد) | 2533aa3c | واگرا و قدیمی — **استفاده نشود**؛ main رسمی روی گیت‌هاب است |
| untracked | ۳۹ فایل (۲۶ سورس‌مانند/۱۳ runtime) | کامیت نشده — فهرست: raw/138/discovery.txt |

repoهای دیگر ۱۳۸: `hypno-fugu-mini` @6805486 (بدون remote، ۱۰۷ untracked!) · `octopus-bridge` @e21f20d (بدون remote، main)

## برد ۱۸۰ — /opt/octopus/*
| repo | SHA/شاخه | وضعیت |
|---|---|---|
| **/opt/octopus/lab** | 76db516 روی `ofn/evolve-20260826-anatomy-180` | ۱ کامیت پوش‌نشده داشت + ۴۱۳ untracked → **preserve شد: `backup/board180-20260830@28209eff`** (۴۳ فایل مستند/کد؛ بقیه evidence است و طبق قواعد کامیت نشد) |
| /opt/octopus/ofn-l4 | 08f9155 master | تمیز، بدون remote، ۱۶ فایل |
| /opt/octopus/a2-lab/sandbox-repo | 029dd40 master | تمیز، ۱ فایل |
| /opt/octopus/lab/llama.cpp-src | f280b26 master | آینهٔ upstream ggml-org — دست نخورده |

## برد ۱۸۲ — /opt/octopus (۶۴۴M) و /opt/octopus-agent (۹۴M)
- **قبل از این اجرا هیچ VCS وجود نداشت.** الان `backup/board182-20260830@294d51c1` = ۷۸۴ فایل (۶.۷M) سورس/تست/اسکیما/دپلوی.
- عمداً خارج‌مانده: venv (۶۳۷M)، RUNS/RECEIPTS/REPORTS/FIXTURES، *.jsonl (ledgerها)، *.log، باینری py-spy — فهرست کامل: raw/182/preserve.log

## لپ‌تاپ (۹ repo — raw/laptop/repos-inventory.txt)
| repo | HEAD | remote |
|---|---|---|
| F:\backup (vault) | ee2ddb5 | germline (E:/germline — **محلی، GitHub نیست**) |
| F:\ofn-node | c1969bc main | origin = ari-OCTOPUS/ofn-node ✓ (+شاخهٔ نگه‌دارندهٔ local/initial-e459e5f) |
| F:\octopus-wire | ca038d4 ofn/wire | (برanch مطابق origin/ofn/wire در گیت‌هاب) |
| F:\octopus-phase0-isolated، F:\backup-deploy-lab، F:\backup-SAFE-2026-07-19، F:\romajan، F:\_______Black Box، C:\Users\Armin | — | بدون remote گیت‌هابی |

## پیوست — ahead/behind تفصیلی هر نود (raw/<node>/branches.txt، 2026-08-30)

### برد ۱۳۸ — /home/ari/ofn
| شاخه | upstream | ahead/behind | آخرین commit |
|---|---|---|---|
| work/truth-record-20260830 (HEAD) | origin/هم‌نام | 0/0 | 08-30 |
| backup/board138-20260830 | origin/هم‌نام | 0/0 | 08-30 |
| audit/cursor-20260828 | origin/هم‌نام | 0/0 | 08-28 |
| ofn-v1.0-three-business-owner-center | origin/هم‌نام | 0/0 | 08-26 |
| **main (محلی برد)** | origin/main | **0 / behind=88** | **08-05** — قدیمی؛ ملاک گیت‌هاب است |
| audit/senior-auditor-20260828-138، discovery/138-body-map، octopus/reconcile، ofn/board-snapshot-20260816، ofn/cockpit-v2-20260827 | NO_UPSTREAM | — | 08-16..08-28 |
| backup/board180-20260830، backup/board182-20260830 (رله دریافت‌شده) | NO_UPSTREAM | — | 08-30 |
| integration/138-business-spine-20260828 | NO_UPSTREAM (بعد از FF) | — | 08-29 |

### برد ۱۸۰ — /opt/octopus/lab (بدون origin — شاخه‌ها NO_UPSTREAM)
| شاخه | آخرین commit |
|---|---|
| backup/board180-20260830 (فعلی) | 08-30 (preserve) |
| ofn/evolve-20260826-anatomy-180 | 08-26 |
| feat/phase3-completion | 08-25 |
| archive/board-life-001-50f31db، experiment/board-life-001 | 08-25 |

### برد ۱۸۲ — /tmp/oct182-preserve-work (scratch؛ شاخهٔ main = snapshot)
بدون تاریخچهٔ قبلی؛ تنها ref = snapshot پوش‌شده.

### untracked تفکیک‌شده (bucket های regex مالک)
| نود | source | tests | runtime | unclassified | جمع |
|---|---|---|---|---|---|
| ۱۳۸ (ofn) | 4 | 0 | 0 | 35 | 39 |
| ۱۸۰ (lab؛ پس از preserve) | 47 | 0 | 273 | 50 | 370 |
| ۱۸۲ (live در برابر branch) | 82 | 0 | 202 | 0 | 284 |
نکته: «unclassified» عمدتاً اسناد evidence با مسیرهایی که با regex bucketها نمی‌خوانند (مثل 06-EVIDENCE/runtime-provenance-*) — نه کد اجرایی.
