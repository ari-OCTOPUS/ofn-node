# KB-11 — Engineering Excellence

> اصول مهندسیِ domain-agnostic از Anthropic «Building Effective Agents» + «Writing Effective Tools». جزئیاتِ معماریِ Brushline در KB-01؛ این سند = اصولِ پایه و anti-pattern.

---

## ۰. اصلِ طلایی
موفق‌ترین پیاده‌سازی‌ها (Coinbase, Intercom, Thomson Reuters) ساده‌اند: composability روی framework. مستقیم با LLM API و الگوهای ساده شروع کن. **تا وقتی workflow کافی است، agent نساز.** (Workflow = مسیرِ ثابت؛ Agent = هدایتِ داینامیک.)

## ۱. Augmented LLM
بلوکِ پایهٔ هر ایجنت: LLM + retrieval + tools + memory. (نگاشتِ Brushline در KB-01 §۲.)

## ۲. پنج الگو (نگاشت در KB-01 §۳)
Prompt Chaining (research→copy→asset) · Routing (cheap-first) · Parallelization (voting برای کپیِ مهم) · Orchestrator-Workers (00-Orchestrator→A–F) · Evaluator-Optimizer (= Constitution Gate). ساده شروع کن، measure کن، پیچیدگی فقط با دلیل.

## ۳. چه چیزی best-in-class را متفاوت می‌کند
۱. **Eval-driven** (نه shipping on vibes). ۲. **Held-out test set** (ضدِ overfit/grounding). ۳. **Tool design:** کم و high-impact، search_x/do_x نه list-all، برگردانِ مرتبط، namespacing. ۴. **Observability:** logging/tracing (الگوی تصمیمِ agentهای non-deterministic). ۵. **Modular:** config مرکزی (پرامپت/Skill). ۶. **MCP** برای اتصالِ tool.

## ۴. Anti-patterns
- framework-زدگی آن‌جا که workflow کافی است.
- agent بدونِ eval کافی.
- consensus را correctness انگاشتن (در صف از Wilson lower-bound برای pass rate استفاده کن، نه نرخِ خام).

## ۵. منابعِ مطالعه
Anthropic Engineering (Building Effective Agents، Writing Tools، Context Engineering)؛ Claude Agent SDK؛ نمونه‌ها: Coinbase/Intercom/Thomson Reuters.

## ۶. نگاشتِ نهاییِ Brushline
هر ایجنت = augmented LLM با toolهای کم/high-impact؛ Orchestrator = orchestrator-workers؛ routing = cheap-first؛ Gate = evaluator-optimizer؛ eval = held-out + observability از روز اول؛ config/کلیدها در پرامپت‌ها هاردکد نشوند (→ CONFIG)؛ integration با ServiceM8/Tradify = consolidate، نه بازسازی.

## قدم بعدی
جزئیات در KB-01 (معماری/tool/integration) و KB-08 (eval).
