import os, json, mimetypes, zipfile, shutil, secrets
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from hypno import __version__
from hypno.config import load
from hypno.adapters.store import Store
from hypno.adapters.rag import seed, retrieve, is_safe_research
from hypno.adapters.brain import Brain
from hypno.adapters.edge_seed import seed_edge_model
from hypno.adapters.telegram import validate, debug as tg_debug, InitDataError
from hypno.kernel.safety import classify, mode_prompt

CATEGORIES = (
    'hypnosis_core', 'math_models', 'neuroscience', 'self_love_training',
    'systems_ai', 'philosophy_symbolism', 'prompts_protocols', 'safety_boundaries'
)

def brain_name(cfg):
    return 'remote:' + cfg.model if cfg.api_key else 'قوانین + منبع'

def _fmt_ts(epoch):
    """تبدیل Unix epoch به رشتهٔ تاریخ/ساعت محلی (YYYY-MM-DD HH:MM)."""
    if not epoch:
        return ''
    try:
        return datetime.fromtimestamp(int(epoch), tz=timezone.utc).strftime('%Y-%m-%d %H:%M')
    except (OSError, ValueError):
        return ''

def _fmt_day(epoch):
    """تبدیل Unix epoch به رشتهٔ روز (YYYY-MM-DD)."""
    return _fmt_ts(epoch)[:10] if epoch else ''

def _slug(text, maxlen=80):
    """تبدیل متن به نام فایل امن."""
    return ''.join(ch if ch.isalnum() or ch in ' -_.' else '-' for ch in (text or 'doc'))[:maxlen]

class App:
    def __init__(self, cfg):
        self.cfg = cfg
        self.store = Store(cfg.db_path)
        self.seeded = seed(self.store, cfg.research_dir)
        self.edge_chunk_count = seed_edge_model(self.store)   # مدل لبهٔ سیستم
        self.brain = Brain(cfg)
        self.download_tokens = {}

    def initdata(self, b):
        return b.get('initData', '') or b.get('_auth', '') or ''

    def user(self, b):
        if self.cfg.bot_token:
            u = validate(self.initdata(b), self.cfg.bot_token)
            uid = str(u.get('id', ''))
            if self.cfg.owners and uid not in self.cfg.owners:
                raise PermissionError('not owner')
            return uid
        return self.cfg.dev_user

    def is_session(self, text):
        return any(w in (text or '') for w in ('شروع', 'هیپنوتیز', 'جلسه', 'القای', 'خودهیپنوتیز'))

    def is_edge_topic(self, text):
        """آیا پیام دربارهٔ مدل لبهٔ سیستم است؟ (تصمیم، خواب، بدن، فلو، فروش،
        مصرف، پول، پرخوری، ابرموجود). اگر چنین است، RAG باید chunks لبه را
        پیدا کند و مغز به مدل ارجاع دهد."""
        return any(w in (text or '') for w in (
            'تصمیم', 'لبه', 'ابرموجود', 'فلو', 'فروش', 'خواب', 'پرخوری', 'مصرف',
            'بدن', 'پول', 'runway', 'حلقه', 'هوس', 'شرم', 'فومو', 'اسکرول',
            'نقاشی', 'کدنویسی', 'خودمدیریت', 'agency', 'decision', 'body', 'edge',
        ))

    def edge_chunks(self, q, limit):
        """مسیر مستقیم برای chunks لبه. FTS کلی chunks قدیمیِ زارش را بالاتر
        رتبه می‌دهد چون متنشان طولانی‌تر است، پس وقتی topic لبه است اول chunks
        لبه را از روی source_url مستقیم با FTS داخلی می‌گیریم، تا مغز حتماً
        مدل را در citations ببیند.

        مثل store.search از OR روی token‌ها استفاده می‌کنیم (نه AND) چون یک
        chunk ممکن است فقط چند کلمه از query را داشته باشد و باز هم مرتبط
        باشد. نیم‌فاصله‌ها و علائم را هم تمیز می‌کنیم."""
        toks = [x.replace('"', '') for x in (q or '').split() if len(x) > 1][:10]
        if not toks:
            return []
        expr = ' OR '.join('"%s"' % x for x in toks)
        with self.store.conn() as db:
            try:
                rows = db.execute(
                    "SELECT d.id,d.title,d.source_url,d.tags,"
                    "snippet(research_fts,1,'','','…',32) text "
                    "FROM research_fts JOIN research_docs d ON d.id=research_fts.rowid "
                    "WHERE research_fts MATCH ? AND d.source_url='local://edge-model' "
                    "ORDER BY rank LIMIT ?",
                    (expr, limit),
                ).fetchall()
            except Exception:
                rows = []
        return [dict(r) for r in rows]

    def query(self, text, mode):
        q = (text or '') + ' ' + mode_prompt(mode)
        if self.is_session(text):
            q += ' خودهیپنوتیزم تلقین تمرکز آرام‌سازی نوروساینس روابط ریاضی ایمنی consent agency hypnosis self hypnosis'
        if self.is_edge_topic(text):
            # کلمات کلیدی مدل لبه تا RAG chunks لبه را پیدا کند
            q += ' مدل لبه سیستم بدن خود ابرموجود فلو بستن حلقه فروش تصمیم خواب مصرف پرخوری agency body superorganism'
        return q

    def panel_note(self, uid, action, extra=None):
        """Record a panel action in the message log WITHOUT calling the brain.

        Previously this issued a hidden `brain.answer` on every write path
        (memory add, research ingest, import, export) — a second brain call
        the user never asked for, billed against quota, with no user-visible
        benefit. It is now a plain log row, which is all an audit trail needs.
        """
        self.store.log(uid, 'assistant', action, {'panel_action': action, 'extra': extra or {}, 'source': 'panel_note'})
        return {'reply': action, 'source': 'panel_note', 'citations': [], 'primed_chunks': 0}

    def session(self, b):
        uid = self.user(b)
        # Accept both the new name and the legacy one so an older client still
        # works after the rename. The new field is the source of truth.
        sa = b.get('safety_acknowledged')
        if sa is None and 'consent' in b:
            sa = b.get('consent')
        s = self.store.session(uid, b.get('mode'), sa)
        return {
            'ok': 1, 'version': __version__, 'user_id': uid, 'session': s,
            'research_docs': self.store.count(), 'brain': brain_name(self.cfg),
            'priming': 'auto-rag-before-hypnosis', 'auth': tg_debug(self.initdata(b)),
            'message': 'پیش‌زمینه آماده است؛ RAG و حافظه قبل از جلسه وارد مغز می‌شوند.'
        }

    def chat(self, b):
        uid = self.user(b)
        text = (b.get('text') or '').strip()
        mode = b.get('mode') or 'calm'
        # Accept both names (see session() above).
        ack = bool(b.get('safety_acknowledged', b.get('consent', False)))
        if not text:
            return {'ok': 0, 'error': 'متن خالی است'}
        self.store.session(uid, mode, ack)
        d = classify(text)
        self.store.log(uid, 'user', text, {'safety': d.level, 'mode': mode})
        if not d.allow:
            return {'ok': 1, 'reply': d.message, 'source': 'safety', 'safety': d.level, 'citations': []}
        if not ack and self.is_session(text):
            return {'ok': 1, 'reply': 'قبل از شروع، رضایت و جای امن را تأیید کن. هر لحظه می‌توانی توقف کنی.', 'source': 'safety', 'safety': 'need_acknowledgement', 'citations': []}
        limit = 12 if self.is_session(text) else 5
        passages = retrieve(self.store, self.query(text, mode), limit)
        # وقتی موضوع لبهٔ سیستم است، chunks لبه را اول بگذار تا مغز حتماً مدل را
        # ببیند. FTS کلی chunks قدیمی را بالاتر می‌آورد، پس مسیر مستقیم می‌زنیم.
        if self.is_edge_topic(text):
            ech = self.edge_chunks(self.query(text, mode), 4)
            seen = {p.get('id') for p in ech}
            rest = [p for p in passages if p.get('id') not in seen]
            passages = (ech + rest)[:limit]
        mem = self.store.memories(uid)
        # نمره‌های ۰-۱۰ لبه را از پیام کاربر بکش؛ مغز می‌تواند به تجزیهٔ مدل ارجاع دهد.
        # در جلسهٔ هیپنوتیزم هم امتحان کن: اگر کاربر نمره‌ای همراه جلسه داده
        # (مثلاً «شروع جلسه، خواب ۳ هوس ۷»)، مدل لبه هم اجرا می‌شود تا جلسه
        # شخصی‌سازی‌شده بدهد، نه فقط یک script ثابت.
        from hypno.adapters.brain import _extract_scores
        is_sess = self.is_session(text)
        scores = _extract_scores(text) if (self.is_edge_topic(text) or is_sess) else None
        r = self.brain.answer(text, mode, mem, passages, d.message, edge_scores=scores)
        self.store.log(uid, 'assistant', r['reply'], r)
        r.update({'ok': 1, 'safety': d.level, 'primed_chunks': len(passages), 'brain_connected': True})
        return r

    def memory(self, b):
        uid = self.user(b)
        i = self.store.add_memory(uid, b.get('kind', 'preference'), b.get('content', ''))
        note = self.panel_note(uid, 'حافظه جدید ذخیره شد')
        return {'ok': 1, 'id': i, 'memories': self.store.memories(uid, 12), 'brain_note': note}

    def research(self, b):
        uid = self.user(b)
        title=b.get('title','منبع علمی آری'); text=b.get('text',''); url=b.get('source_url','user://ari')
        tags=b.get('tags','user science math hypnosis')
        if not is_safe_research(title,text,tags,url):
            return {'ok':0,'error':'منبع به پروژه خودهیپنوتیزمی امن مربوط نیست یا کنار گذاشته شده است.','code':'research_rejected'}
        i = self.store.add_research(title, text, url, 'user', tags)
        self.store.log(uid, 'system', 'manual_research_ingest', {'id': i})
        note = self.panel_note(uid, 'منبع پژوهشی جدید به RAG اضافه شد')
        return {'ok': 1, 'id': i, 'research_docs': self.store.count(), 'brain_note': note}

    def research_stats(self):
        out = {'ok': 1, 'total': self.store.count(), 'categories': {}, 'source_types': {}, 'manifest': None, 'brain': brain_name(self.cfg)}
        with self.store.conn() as db:
            for r in db.execute('SELECT source_type,COUNT(*) n FROM research_docs GROUP BY source_type'):
                out['source_types'][r['source_type']] = r['n']
            rows = db.execute('SELECT tags FROM research_docs').fetchall()
        for c in CATEGORIES:
            out['categories'][c] = sum(1 for r in rows if c in (r['tags'] or ''))
        mp = os.path.join(self.cfg.root, 'research_import', 'reports', 'summary.json')
        if os.path.exists(mp):
            try:
                out['manifest'] = json.load(open(mp, encoding='utf-8'))
            except Exception as e:
                out['manifest_error'] = str(e)
        return out

    def research_list(self, qs):
        q = (qs.get('q') or [''])[0]
        cat = (qs.get('category') or [''])[0]
        try:
            limit = min(int((qs.get('limit') or ['50'])[0] or 50), 200)
        except Exception:
            limit = 50
        if q:
            return {'ok': 1, 'results': retrieve(self.store, q, limit), 'brain': brain_name(self.cfg)}
        sql = 'SELECT id,title,source_url,source_type,tags,substr(text,1,420) text FROM research_docs'
        args = []
        if cat:
            sql += ' WHERE tags LIKE ?'
            args.append('%' + cat + '%')
        sql += ' ORDER BY id DESC LIMIT ?'
        args.append(limit)
        with self.store.conn() as db:
            rows = [dict(r) for r in db.execute(sql, args)]
        return {'ok': 1, 'results': rows, 'brain': brain_name(self.cfg)}

    def rebuild_fts(self):
        with self.store.conn() as db:
            db.execute("INSERT INTO research_fts(research_fts) VALUES('rebuild')")
        return {'ok': 1, 'research_docs': self.store.count()}

    def import_research(self, b):
        uid = self.user(b)
        p = os.path.join(self.cfg.root, 'research_import', 'rag_import.jsonl')
        if not os.path.exists(p):
            return {'ok': 0, 'error': 'research_import/rag_import.jsonl پیدا نشد'}
        with self.store.conn() as db:
            db.execute("DELETE FROM research_docs WHERE source_url LIKE 'attachment://pasted_text_178593%'")
            db.execute("INSERT INTO research_fts(research_fts) VALUES('rebuild')")
        n=0; skipped=0
        for line in open(p, encoding='utf-8'):
            d=json.loads(line)
            text='[category: {}]\n[section: {}]\n[source: {}]\n\n{}'.format(d.get('category'),d.get('section'),d.get('source_url'),d.get('text',''))
            tags=(d.get('tags','')+' '+d.get('category','')+' '+d.get('primary_category','')).strip()
            if not is_safe_research(d.get('title',''),text,tags,d.get('source_url','')): skipped+=1; continue
            self.store.add_research(d['title'][:240],text,d.get('source_url',''),'attachment_chunk',tags); n+=1
        self.rebuild_fts()
        self.store.log(uid, 'system', f'research_imported:{n}', {'path': p, 'skipped': skipped})
        note = self.panel_note(uid, 'import/rebuild پژوهش انجام شد')
        return {'ok': 1, 'imported_chunks': n, 'skipped_chunks': skipped, 'research_docs': self.store.count(), 'brain_note': note}

    def research_delete(self, b):
        """حذف یک سند پژوهشی با id — فقط owner."""
        uid = self.user(b)
        if self.cfg.owners and uid not in self.cfg.owners:
            raise PermissionError('not owner')
        try:
            doc_id = int(b.get('id'))
        except (TypeError, ValueError):
            return {'ok': 0, 'error': 'id لازم است'}
        ok = self.store.delete_research(doc_id)
        return {'ok': 1 if ok else 0, 'message': 'حذف شد' if ok else 'پیدا نشد'}

    def research_cleanup(self, b):
        """پاک‌سازی خودکار نویز/تکراری/تگ."""
        uid = self.user(b)
        result = self.store.cleanup_research()
        return {'ok': 1, 'cleanup': result, 'research_docs': self.store.count()}

    def research_summary(self, b):
        """خلاصهٔ یک سند با مغز ریموت (۲ جمله)."""
        uid = self.user(b)
        try:
            doc_id = int(b.get('id'))
        except (TypeError, ValueError):
            return {'ok': 0, 'error': 'id لازم است'}
        with self.store.conn() as db:
            r = db.execute("SELECT title,text FROM research_docs WHERE id=?", (doc_id,)).fetchone()
        if not r:
            return {'ok': 0, 'error': 'سند پیدا نشد'}
        text = (r['text'] or '')[:2000]
        try:
            reply = self.brain.answer(
                f"این متن را در دو جملهٔ سادهٔ فارسی خلاصه کن:\n\n{text}",
                'learn', [], [], 'safe')
            return {'ok': 1, 'title': r['title'], 'summary': reply.get('reply', '')}
        except Exception as e:
            return {'ok': 0, 'error': str(e)}

    def edge_quiz_new(self, b):
        """یک سناریوی کوییز جدید بساز (بدون مغز، فقط محلی)."""
        uid = self.user(b)
        import random
        from hypno.kernel import edge
        # سناریوی رندوم اما واقع‌گرا
        b_val = random.choice([2, 3, 3, 4, 5, 7, 8])
        c_val = random.choice([3, 4, 5, 6, 7, 8])
        x_val = random.choice([2, 3, 4, 5, 6, 7, 8])
        v = edge.daily_verdict(b_val / 10.0, c_val / 10.0, x_val / 10.0)
        # توضیح فارسی
        explanations = {
            'سبز': 'خواب کافی + خود قوی + ابرموجود متعادل = روز پایدار.',
            'زرد': 'یکی از قطب‌ها ضعیف است؛ احتیاط کن.',
            'قرمز': 'بدن غالب یا همه ضعیف؛ امروز استراحت کن، تصمیم بزرگ نگیر.',
            'خنثی': 'داده‌ها حد واسط؛ حکم قطعی نیست.',
        }
        scenario = {
            'b': b_val, 'c': c_val, 'x': x_val,
            'verdict': v.verdict,
            'explanation': explanations.get(v.verdict, v.advice),
        }
        return {'ok': 1, 'scenario': {'b': b_val, 'c': c_val, 'x': x_val}, 'answer': v.verdict, 'explanation': explanations.get(v.verdict, v.advice)}

    def lab_record(self, b):
        """ثبت نتیجهٔ آزمایشگاه (برای nightly sync)."""
        uid = self.user(b)
        kind = str(b.get('kind') or '').strip()
        if kind not in ('daily', 'decision', 'quiz'):
            return {'ok': 0, 'error': 'نوع آزمایش درست نیست'}
        payload = b.get('payload') or {}
        self.store.add_lab_result(uid, kind, payload)
        return {'ok': 1, 'message': 'ثبت شد'}

    def brain_status(self, b):
        uid = self.user(b)
        mode = b.get('mode') or 'calm'
        q = 'خودهیپنوتیزم حافظه پژوهش پنل ' + mode
        passages = retrieve(self.store, self.query(q, mode), 8)
        mem = self.store.memories(uid, 12)
        with self.store.conn() as db:
            mc = db.execute('SELECT COUNT(*) FROM messages WHERE user_id=?', (uid,)).fetchone()[0]
            mm = db.execute('SELECT COUNT(*) FROM memories WHERE user_id=? AND active=1', (uid,)).fetchone()[0]
            last = [dict(r) for r in db.execute('SELECT role,substr(content,1,180) content,created_at FROM messages WHERE user_id=? ORDER BY id DESC LIMIT 6', (uid,))]
        return {'ok': 1, 'user_id': uid, 'brain': brain_name(self.cfg), 'connected': True, 'memory_count': mm, 'message_count': mc, 'research_docs': self.store.count(), 'priming_preview': len(passages), 'memories': mem, 'last_messages': last, 'citations': passages[:5]}

    def obsidian_export(self, b):
        uid = self.user(b)
        vault = os.path.join(self.cfg.root, 'obsidian-vault', 'Hypno-Fugu-Vault')
        exp = os.path.join(self.cfg.root, 'exports')
        os.makedirs(exp, exist_ok=True)
        if os.path.exists(vault):
            shutil.rmtree(vault)
        for rel in ('Research/Cleaned', 'Research/Raw', 'Sources', 'Memory',
                     'Sessions', 'Daily', 'Edge', '.obsidian'):
            os.makedirs(os.path.join(vault, rel), exist_ok=True)
        def w(rel, txt):
            p = os.path.join(vault, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, 'w', encoding='utf-8').write(txt)

        # ── Dashboard ──────────────────────────────────────────────────
        now_iso = datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M')
        with self.store.conn() as db:
            mem_count = db.execute('SELECT COUNT(*) FROM memories WHERE user_id=? AND active=1', (uid,)).fetchone()[0]
            msg_count = db.execute('SELECT COUNT(*) FROM messages WHERE user_id=?', (uid,)).fetchone()[0]
            note_count = db.execute('SELECT COUNT(*) FROM daily_notes WHERE user_id=?', (uid,)).fetchone()[0]
        w('00-Dashboard.md', (
            '# آرام‌جا — خروجی ابسیدین\n\n'
            f'- تاریخ تولید: {now_iso}\n'
            f'- منابع: {self.store.count()}\n'
            f'- حافظه: {mem_count}\n'
            f'- پیام: {msg_count}\n'
            f'- یادداشت روزانه: {note_count}\n'
            f'- مغز: {brain_name(self.cfg)}\n'
            '\n## نقشهٔ محتوا\n'
            '- [[Research/MOC-Research|پژوهش]]\n'
            '- [[Sources/MOC-Sources|منابع]]\n'
            '- [[Memory/MOC-Memory|حافظه]]\n'
            '- [[Sessions/MOC-Sessions|جلسات]]\n'
            '- [[Edge/MOC-Edge|امتیازات روزانه]]\n'
        ))

        # ── Research / Cleaned ─────────────────────────────────────────
        src = os.path.join(self.cfg.root, 'research_import', 'cleaned')
        links = []
        if os.path.isdir(src):
            for name in sorted(os.listdir(src)):
                if name.endswith('.md'):
                    shutil.copy2(os.path.join(src, name),
                                 os.path.join(vault, 'Research', 'Cleaned', name))
                    links.append(f'- [[Cleaned/{name[:-3]}|{name[:-3]}]]')
        w('Research/MOC-Research.md',
          '# نقشهٔ پژوهش\n\n' + ('\n'.join(links) or '_هنوز سندی نیست._') + '\n')

        # ── Research / Raw ────────────────────────────────────────────
        raw = os.path.join(self.cfg.root, 'research_import', 'raw')
        if os.path.isdir(raw):
            for name in sorted(os.listdir(raw)):
                if name.endswith('.txt'):
                    txt = open(os.path.join(raw, name),
                               encoding='utf-8', errors='ignore').read()
                    w('Research/Raw/' + name[:-4] + '.md',
                      f'---\ntype: raw\nsource: {name}\n---\n\n'
                      f'```text\n{txt}\n```\n')

        # ── کوئری داده‌ها ────────────────────────────────────────────
        with self.store.conn() as db:
            rows = [dict(r) for r in db.execute(
                'SELECT id,title,source_url,source_type,tags,'
                'substr(text,1,5000) text FROM research_docs ORDER BY id')]
            mem = [dict(r) for r in db.execute(
                'SELECT kind,content,created_at FROM memories '
                'WHERE user_id=? AND active=1 ORDER BY created_at DESC', (uid,))]
            msgs = [dict(r) for r in db.execute(
                'SELECT role,content,created_at FROM messages '
                'WHERE user_id=? ORDER BY id DESC LIMIT 200', (uid,))]
            notes = [dict(r) for r in db.execute(
                'SELECT day,content,created_at FROM daily_notes '
                'WHERE user_id=? ORDER BY day DESC', (uid,))]
            lab_rows = [dict(r) for r in db.execute(
                "SELECT kind,payload,created_at FROM lab_results "
                "WHERE user_id=? ORDER BY created_at DESC LIMIT 100", (uid,))]
        edge_rows = self.store.edge_history(uid, limit=30)

        # ── Sources (قبلاً RAG-Chunks) ─────────────────────────────────
        src_links = []
        for r in rows:
            title = _slug(r['title'])
            w(f"Sources/{r['id']:04d}-{title}.md",
              f"---\ntype: source\nid: {r['id']}\n"
              f"source_type: {r['source_type']}\n"
              f"tags: {json.dumps((r['tags'] or '').split(), ensure_ascii=False)}\n"
              f"source_url: {r['source_url']}\n---\n\n"
              f"# {r['title']}\n\n{r['text']}\n")
            src_links.append(f'- [[{r["id"]:04d}-{title}|{r["title"] or "بدون عنوان"}]]')
        w('Sources/MOC-Sources.md',
          '# نقشهٔ منابع\n\n' + ('\n'.join(src_links) or '_منبعی نیست._') + '\n')

        # ── Memory ───────────────────────────────────────────────────
        mem_lines = []
        for m in mem:
            ts = _fmt_ts(m['created_at'])
            mem_lines.append(f"- **{m['kind']}**{f' ({ts})' if ts else ''}: {m['content']}")
        w('Memory/MOC-Memory.md',
          '# حافظه\n\n' + ('\n'.join(mem_lines) if mem_lines else '_حافظه‌ای ثبت نشده._') + '\n')

        # ── Sessions (اسپلیت به تفکیک روز) ────────────────────────────
        from collections import defaultdict
        by_day = defaultdict(list)
        for m in msgs:
            day = _fmt_day(m['created_at']) or 'unknown'
            by_day[day].append(m)
        sess_links = []
        for day in sorted(by_day.keys()):
            day_msgs = by_day[day]
            sections = '\n\n'.join(
                f"## {m['role']}\n\n{m['content']}" for m in day_msgs)
            w(f'Sessions/{day}.md',
              f'---\ntype: session_log\ndate: {day}\n'
              f'messages: {len(day_msgs)}\n---\n\n'
              f'# جلسات {day}\n\n{sections}\n')
            sess_links.append(f'- [[Sessions/{day}|{day}]] — {len(day_msgs)} پیام')
        w('Sessions/MOC-Sessions.md',
          '# نقشهٔ جلسات\n\n'
          + ('\n'.join(sess_links) if sess_links else '_جلساتی نیست._') + '\n')

        # ── Daily Notes ──────────────────────────────────────────────
        by_note_day = defaultdict(list)
        for n in notes:
            by_note_day[n['day']].append(n)
        for day in sorted(by_note_day.keys()):
            entries = by_note_day[day]
            parts = []
            for i, e in enumerate(entries):
                header = f'## یادداشت {i + 1}' if len(entries) > 1 else '## یادداشت'
                parts.append(f'{header}\n\n{e["content"]}')
            w(f'Daily/{day}.md',
              f'---\ntype: daily_note\ndate: {day}\nentries: {len(entries)}\n---\n\n'
              + '\n\n---\n\n'.join(parts) + '\n')

        # ── Edge (امتیازات روزانه + نتایج آزمایشگاه) ───────────────
        edge_lines = []
        if edge_rows:
            edge_lines.append('| روز | بدن | خود | ابرموجود | حکم |')
            edge_lines.append('|---|---|---|---|---|')
            for e in edge_rows:
                edge_lines.append(
                    f"| {e['day']} | {e['b']:.0f} | {e['c']:.0f} "
                    f"| {e['x']:.0f} | {e.get('verdict', '-')} |")
        else:
            edge_lines.append('_امتیازی ثبت نشده._')

        # نتایج آزمایشگاه
        quiz_lines = []
        decision_lines = []
        for lr in lab_rows:
            try:
                payload = json.loads(lr['payload']) if isinstance(lr['payload'], str) else lr['payload']
            except Exception:
                payload = {}
            ts = _fmt_ts(lr['created_at'])
            if lr['kind'] == 'quiz':
                correct = '✅' if payload.get('correct') else '❌'
                quiz_lines.append(
                    f"- {ts}: حدس={payload.get('guess', '?')} "
                    f"جواب={payload.get('answer', '?')} {correct}")
            elif lr['kind'] == 'decision':
                decision_lines.append(
                    f"- {ts}: غالب={payload.get('dominant', '?')} "
                    f"بدن={payload.get('body_share', 0):.0%} "
                    f"خود={payload.get('self_share', 0):.0%} "
                    f"ابرموجود={payload.get('super_share', 0):.0%}")

        edge_content = '# نقشهٔ امتیازات روزانه\n\n'
        edge_content += '## نمرات لبه\n\n' + '\n'.join(edge_lines) + '\n'
        if quiz_lines:
            edge_content += '\n## نتایج کوییز\n\n' + '\n'.join(quiz_lines) + '\n'
        if decision_lines:
            edge_content += '\n## نتایج تصمیم\n\n' + '\n'.join(decision_lines) + '\n'
        w('Edge/MOC-Edge.md', edge_content)

        # ── .obsidian configs ─────────────────────────────────────────
        w('.obsidian/app.json',
          '{"legacyEditor":false,"livePreview":true}\n')
        w('.obsidian/core-plugins.json', json.dumps([
            'graph', 'search', 'daily-notes', 'tag-pane', 'outline',
        ], ensure_ascii=False) + '\n')
        w('.obsidian/daily-notes.json', json.dumps({
            'folder': 'Daily',
            'template': '',
            'format': 'YYYY-MM-DD',
        }, ensure_ascii=False) + '\n')

        # ── ZIP ───────────────────────────────────────────────────────
        zip_path = os.path.join(exp, 'hypno-fugu-obsidian-vault.zip')
        if os.path.exists(zip_path):
            os.remove(zip_path)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
            for root, dirs, files in os.walk(vault):
                for f in files:
                    p = os.path.join(root, f)
                    z.write(p, os.path.relpath(p, os.path.dirname(vault)))
        note = self.panel_note(uid, 'خروجی قابل‌حمل ابسیدین ساخته شد')
        token = secrets.token_urlsafe(24)
        self.download_tokens[token] = zip_path
        self.download_tokens = dict(list(self.download_tokens.items())[-20:])
        return {
            'ok': 1, 'vault_path': vault, 'zip_path': zip_path,
            'download_url': '/exports/hypno-fugu-obsidian-vault.zip?token=' + token,
            'files': sum(len(files) for _, _, files in os.walk(vault)),
            'brain_note': note,
        }

    # ── مدل لبهٔ سیستم: endpointهای تعاملی ─────────────────────────────────
    # این سه endpoint به کاربر اجازه می‌دهند نمرهٔ ۰-۱۰ بدهد و نتیجهٔ مدل را
    # بگیرد. مغز هم در chat از همان مدل استفاده می‌کند (edge_scores).
    def edge_decision(self, b):
        from hypno.kernel import edge
        uid = self.user(b)
        keys = ('V', 'P', 'K', 'D', 'H', 'E', 'F', 'M', 'U', 'C',
                'sleep_debt', 'stress')
        defaults = {k: 5 for k in keys}        # نمرهٔ خنثی برای متغیرهای غایب
        for k in keys:
            v = b.get(k)
            if v is not None:
                try:
                    defaults[k] = max(0, min(10, float(v)))
                except (TypeError, ValueError):
                    pass
        r = edge.decision_source(
            defaults['V'], defaults['P'], defaults['K'], defaults['D'],
            defaults['H'], defaults['E'], defaults['F'], defaults['M'],
            defaults['U'], defaults['C'], defaults['sleep_debt'],
            defaults['stress'],
        )
        return {
            'ok': 1, 'user_id': uid,
            'ai': round(r.ai, 3), 'si': round(r.si, 3), 'bi': round(r.bi, 3),
            'a_self': round(r.dec.a_self, 3), 'a_super': round(r.dec.a_super, 3),
            'a_body': round(r.dec.a_body, 3),
            'dominant': r.dec.dominant(),
            'verdict': r.verdict,
            'healthy': round(r.healthy, 3),
        }

    def edge_daily(self, b):
        from hypno.kernel import edge
        uid = self.user(b)
        try:
            bb = max(0.0, min(10.0, float(b.get('B', 5))))
            cc = max(0.0, min(10.0, float(b.get('C', 5))))
            xx = max(0.0, min(10.0, float(b.get('X', 5))))
        except (TypeError, ValueError):
            return {'ok': 0, 'error': 'نمره‌های B و C و X باید عدد ۰ تا ۱۰ باشند.'}
        v = edge.daily_verdict(bb, cc, xx)
        self.store.log_edge_daily(uid, bb, cc, xx, v.verdict)
        # streak: چند روز اخیر همین حکم بوده
        hist = self.store.edge_history(uid, 14)
        verdicts = [h.get('verdict') for h in hist]
        streak = 0
        for vd in reversed(verdicts):
            if vd in ('زرد', 'قرمز'):
                streak += 1
            else:
                break
        red = edge.three_red_days([
            edge.DailyVerdict(h.get('verdict', 'سبز'), '') for h in hist
        ]) if len(hist) >= 3 else edge.DailyVerdict('خنثی', 'هنوز دادهٔ کافی نیست.')
        return {
            'ok': 1, 'user_id': uid,
            'b': bb, 'c': cc, 'x': xx,
            'verdict': v.verdict, 'advice': v.advice,
            'streak': streak, 'red_flag': red.verdict,
        }

    def daily_note(self, b):
        """ثبت یک یادداشت روزانهٔ جدید."""
        uid = self.user(b)
        content = (b.get('content') or '').strip()
        if not content:
            return {'ok': 0, 'error': 'یادداشت خالی است'}
        note = self.store.add_daily_note(uid, content)
        return {'ok': 1, 'note': note, 'message': 'یادداشت ثبت شد'}

    def daily_notes_list(self, b):
        """لیست یادداشت‌های اخیر."""
        uid = self.user(b)
        try:
            limit = max(1, min(200, int(b.get('limit', 50))))
        except (TypeError, ValueError):
            limit = 50
        notes = self.store.daily_notes(uid, limit=limit)
        return {'ok': 1, 'notes': notes, 'count': len(notes)}

    def daily_note_delete(self, b):
        """حذف یک یادداشت با id."""
        uid = self.user(b)
        try:
            note_id = int(b.get('id'))
        except (TypeError, ValueError):
            return {'ok': 0, 'error': 'id یادداشت لازم است'}
        ok = self.store.delete_daily_note(uid, note_id)
        if not ok:
            return {'ok': 0, 'error': 'یادداشت پیدا نشد'}
        # اگر این یادداشت به RAG منتقل شده بود، آن chunk را هم پاک کن
        src = f'local://daily-note/{note_id}'
        self.store.delete_research_by_source(src)
        return {'ok': 1, 'message': 'یادداشت حذف شد'}

    def edge_history(self, b):
        uid = self.user(b)
        try:
            limit = max(1, min(90, int(b.get('limit', 14))))
        except (TypeError, ValueError):
            limit = 14
        days = self.store.edge_history(uid, limit)
        return {'ok': 1, 'user_id': uid, 'days': days}

    def health(self):
        return {'ok': 1, 'name': 'hypno-fugu-mini', 'version': __version__, 'db': self.cfg.db_path, 'research_docs': self.store.count(), 'port': self.cfg.port, 'brain': brain_name(self.cfg)}

def handler(app):
    class H(BaseHTTPRequestHandler):
        def out(self, obj, code=200, ctype='application/json; charset=utf-8'):
            data = obj if isinstance(obj, bytes) else json.dumps(obj, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header('Content-Type', ctype)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Cache-Control', 'no-store, max-age=0')
            self.end_headers()
            self.wfile.write(data)
        def body(self):
            n = int(self.headers.get('Content-Length', '0') or 0)
            if n > 400000:
                raise ValueError('body too large')
            b = json.loads(self.rfile.read(n) or b'{}')
            a = self.headers.get('Authorization', '')
            if a.startswith('tma ') and not b.get('initData'):
                b['initData'] = a[4:]
            return b
        def require_qs_user(self, qs):
            init = (qs.get('initData') or [''])[0]
            auth = self.headers.get('Authorization', '')
            if auth.startswith('tma ') and not init: init = auth[4:]
            try:
                app.user({'initData': init}); return True
            except Exception:
                return False
        def do_GET(self):
            p = urlparse(self.path); qs = parse_qs(p.query)
            if p.path == '/health':
                return self.out(app.health())
            if p.path == '/api/research/search':
                if not self.require_qs_user(qs): return self.out({'ok':0,'error':'auth required'},401)
                return self.out({'ok': 1, 'results': retrieve(app.store, (qs.get('q') or [''])[0], 8)})
            if p.path == '/api/research/stats':
                if not self.require_qs_user(qs): return self.out({'ok':0,'error':'auth required'},401)
                return self.out(app.research_stats())
            if p.path == '/api/research/list':
                if not self.require_qs_user(qs): return self.out({'ok':0,'error':'auth required'},401)
                return self.out(app.research_list(qs))
            if p.path == '/api/edge/history':
                if not self.require_qs_user(qs): return self.out({'ok':0,'error':'auth required'},401)
                init = (qs.get('initData') or [''])[0]
                return self.out(app.edge_history({'initData': init,
                                                  'limit': (qs.get('limit') or [14])[0]}))
            if p.path.startswith('/exports/'):
                token = (qs.get('token') or [''])[0]
                full = app.download_tokens.get(token)
                root = os.path.abspath(os.path.join(app.cfg.root, 'exports')) + os.sep
                if not token or not full or not os.path.abspath(full).startswith(root) or not os.path.isfile(full):
                    return self.out({'ok': 0, 'error': 'forbidden'}, 403)
                return self.out(open(full, 'rb').read(), 200, 'application/zip')
            path = '/index.html' if p.path in ('/', '') else p.path
            full = os.path.abspath(os.path.join(app.cfg.web_root, path.lstrip('/')))
            root = os.path.abspath(app.cfg.web_root) + os.sep
            if not full.startswith(root) or not os.path.isfile(full):
                return self.out({'ok': 0, 'error': 'not found'}, 404)
            data = open(full, 'rb').read()
            c = mimetypes.guess_type(full)[0] or 'application/octet-stream'
            return self.out(data, 200, 'text/html; charset=utf-8' if full.endswith('.html') else c)
        def do_POST(self):
            try:
                b = self.body()
                routes = {
                    '/api/session': app.session,
                    '/api/chat': app.chat,
                    '/api/memory': app.memory,
                    '/api/research/ingest': app.research,
                    '/api/research/import': app.import_research,
                    '/api/research/rebuild': lambda x: app.rebuild_fts(),
                    '/api/research/delete': app.research_delete,
                    '/api/research/cleanup': app.research_cleanup,
                    '/api/research/summary': app.research_summary,
                    '/api/edge/quiz': app.edge_quiz_new,
                    '/api/lab/record': app.lab_record,
                    '/api/brain/status': app.brain_status,
                    '/api/obsidian/export': app.obsidian_export,
                    '/api/edge/decision': app.edge_decision,
                    '/api/edge/daily': app.edge_daily,
                    '/api/daily-note': app.daily_note,
                    '/api/daily-notes': app.daily_notes_list,
                    '/api/daily-note/delete': app.daily_note_delete,
                }
                fn = routes.get(urlparse(self.path).path)
                return self.out(fn(b) if fn else {'ok': 0, 'error': 'not found'}, 200 if fn else 404)
            except InitDataError as e:
                return self.out({'ok': 0, 'error': e.message, 'code': e.code}, 401)
            except PermissionError as e:
                return self.out({'ok': 0, 'error': str(e), 'code': 'not_owner'}, 403)
            except Exception as e:
                return self.out({'ok': 0, 'error': str(e), 'code': 'server_error'}, 400)
    return H

def main():
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument('--check', action='store_true')
    a = ap.parse_args(); cfg = load(); app = App(cfg)
    if a.check:
        print(json.dumps(app.health(), ensure_ascii=False, indent=2)); return
    print(f'hypno-fugu-mini listening on http://{cfg.host}:{cfg.port}')
    ThreadingHTTPServer((cfg.host, cfg.port), handler(app)).serve_forever()
if __name__ == '__main__':
    main()
