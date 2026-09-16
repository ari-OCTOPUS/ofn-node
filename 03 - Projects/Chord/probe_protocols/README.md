# probe_protocols — آزمایش‌های کوچکِ کم‌خطرِ لایهٔ تحقیقِ Chord

قاعده: هر probe یک فایلِ `PRB-###-<slug>.md` با این ساختار:

- **فرضیهٔ هدف:** ارجاع به H-### در `../hypothesis_registry.md`
- **طرح:** کوچک‌ترین آزمایشِ read-only/برگشت‌پذیر (هرگز پول/secret/کدِ زنده)
- **متریکِ موفقیت/شکست:** از قبل، عددی، بدونِ جای مذاکره بعد از دیدنِ نتیجه
- **داده:** فقط ledger سایهٔ chord (`_ops/chord/state/chord-ledger.jsonl`) و outcomeهای ثبت‌شده
- **نتیجه:** تاریخ + عدد + حکم (supported/rejected) + لینک به رکوردها

اولین probe طبیعی: **PRB-001** — بعد از فاز C، مقایسهٔ verdictهای سایهٔ chord با outcome
واقعیِ همان missionها (تستِ قرمز/سبز، rollback، هزینه) در برابرِ baseline تصادفی/دکترِ تنها.
