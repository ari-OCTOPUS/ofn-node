"""Persisted local RAG memory for Saba's studio assistant."""
from __future__ import annotations
import hashlib, json, random, re
from .sqlite_base import Pool, apply_schema

SCHEMA=("""
CREATE TABLE IF NOT EXISTS assistant_chunks(
 tenant_id TEXT NOT NULL, chunk_id TEXT PRIMARY KEY,
 source TEXT NOT NULL, title TEXT NOT NULL DEFAULT '',
 body TEXT NOT NULL, body_lc TEXT NOT NULL, created_at INTEGER NOT NULL)
""",
"CREATE INDEX IF NOT EXISTS assistant_chunks_tenant ON assistant_chunks(tenant_id,source)",
"""
CREATE TABLE IF NOT EXISTS assistant_runs(
 run_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, source TEXT NOT NULL,
 status TEXT NOT NULL, detail TEXT NOT NULL DEFAULT '', created_at INTEGER NOT NULL)
""",
"""
CREATE TABLE IF NOT EXISTS assistant_chat_turns(
 turn_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, user_text TEXT NOT NULL,
 assistant_text TEXT NOT NULL, sources_json TEXT NOT NULL DEFAULT '[]', created_at INTEGER NOT NULL)
""",
"CREATE INDEX IF NOT EXISTS assistant_chat_tenant_time ON assistant_chat_turns(tenant_id,created_at)")

_WORD=re.compile(r"[\w\u0600-\u06FF]{3,}", re.UNICODE)
SAFETY=("فقط توصیهٔ سطح‌بالا، امن و قانونی بده؛ دربارهٔ دورزدن قوانین، عدم رضایت، "
        "فریب، محتوای غیرقانونی یا افشای حریم خصوصی راهنمایی نده.")

class StudioAssistantStore:
    def __init__(self, path: str, shared_memory=None):
        """`shared_memory` is an optional `fugu_core.memory.Memory`.

        When wired, `answer_local` falls back to the shared corpus when the
        local chunks have nothing for a question. The corpus is read-only
        here — OFN never writes to it through this store; the daily assistant
        refresh writes via its own ingest path. `None` keeps the old behaviour
        exactly, so tests that don't pass one are unaffected.
        """
        self._pool = Pool(path); apply_schema(self._conn, SCHEMA)
        self._shared = shared_memory
    @property
    def _conn(self): return self._pool.conn
    def close(self): self._pool.close()
    def _terms(self,text):
        return [w.lower() for w in _WORD.findall(text or "") if len(w)>2]
    def ingest_text(self, tenant, source, title, text, *, now_epoch_s):
        parts=[]; cur=''
        for para in re.split(r'\n\s*\n+', text or ''):
            para=para.strip()
            if not para: continue
            if cur and len(cur)+len(para)>1800:
                parts.append(cur); cur=para
            else:
                cur=(cur+'\n\n'+para).strip()
        if cur: parts.append(cur)
        return self._put(tenant, source, title, parts, now_epoch_s=now_epoch_s)
    def _put(self, tenant, source, title, parts, *, now_epoch_s):
        n=0; self._conn.execute('BEGIN IMMEDIATE')
        try:
            for body in parts:
                cid=hashlib.sha256((tenant+'|'+source+'|'+body).encode()).hexdigest()[:32]
                self._conn.execute('INSERT OR REPLACE INTO assistant_chunks VALUES (?,?,?,?,?,?,?)',
                    (tenant,cid,source,str(title or '')[:120],body,body.lower(),int(now_epoch_s)))
                n+=1
            self._conn.execute('COMMIT')
        except Exception:
            self._conn.execute('ROLLBACK'); raise
        return n
    def search(self, tenant, question, *, limit=4):
        terms=self._terms(question)
        rows=list(self._conn.execute('SELECT chunk_id,source,title,body,body_lc,created_at FROM assistant_chunks WHERE tenant_id=?',(tenant,)))
        scored=[]
        for r in rows:
            body=str(r['body_lc']); score=sum(body.count(t) for t in terms)
            if score or not terms: scored.append((score,int(r['created_at']),r))
        scored.sort(key=lambda x:(x[0],x[1]), reverse=True)
        return [{'id':r['chunk_id'],'source':r['source'],'title':r['title'],'body':r['body']} for _,_,r in scored[:limit]]
    def random_help(self, tenant, *, limit=3):
        rows=list(self._conn.execute('SELECT chunk_id,source,title,body FROM assistant_chunks WHERE tenant_id=?',(tenant,)))
        random.shuffle(rows)
        return [{'id':r['chunk_id'],'source':r['source'],'title':r['title'],'body':r['body']} for r in rows[:limit]]
    def answer_local(self, tenant, question):
        q=(question or '').strip()
        ctx=self.search(tenant,q,limit=4) if q else self.random_help(tenant,limit=3)
        if not ctx:
            rows=list(self._conn.execute('SELECT chunk_id,source,title,body FROM assistant_chunks LIMIT 4'))
            ctx=[{'id':r['chunk_id'],'source':r['source'],'title':r['title'],'body':r['body']} for r in rows]
        # Shared-corpus fallback: when this tenant's own chunks say nothing,
        # the shared knowledge (edge model, hypno research, cross-tenant
        # seeds) may still answer. Read-only here. The tenant's own answer is
        # always preferred; shared is only a wider net for empty cases.
        if not ctx and self._shared is not None and q:
            try:
                hits = self._shared.recall(tenant, q, limit=4)
                if hits:
                    ctx = [{'id': h.chunk_id, 'source': 'shared:' + (h.source_url or ''),
                            'title': h.title, 'body': h.body} for h in hits]
            except Exception:
                # Shared memory is a bonus, never a dependency. If it is
                # unavailable the local answer path proceeds unchanged.
                pass
        if not ctx:
            return {'answer':'فعلاً چیزی برای پیشنهاد ندارم؛ یه متن یا ایده بده تا کمکت کنم.','sources':[],'mode':'empty'}
        blob=' '.join([q]+[c['body'][:900] for c in ctx]).lower()
        tips=[]
        if any(w in blob for w in ['قیمت','subscription','ppv','tip','پول','درآمد','اشتراک']):
            tips.append('برای شروع، قیمت رو ساده و سبک بذار؛ بعد که جا افتادی، کم‌کم حالت‌های دیگه رو امتحان کن.')
        if any(w in blob for w in ['عکس','نور','گالری','پا','محتوا','کپشن','عکاسی']):
            tips.append('برای عکس امروز یه حس روشن انتخاب کن: نور نرم، پس‌زمینه خلوت و یه حس قشنگ.')
        if any(w in blob for w in ['امن','حریم','privacy','قانون','خصوصی','هویت']):
            tips.append('قبل از انتشار، یه بار عکس رو نگاه کن؛ چیزی خصوصی، هویت یا لوکیشن نباید لو بره.')
        if not tips:
            tips.extend([
                'امروز فقط سه تا عکس قشنگ انتخاب کن؛ لازم نیست همه‌چیز کامل باشه.',
                'یه کپشن کوتاه و خودمونی بنویس؛ مثل حرف زدن با یه دوست صمیمی.',
                'اگه حوصله نداری، فقط آلبوم عکس‌هاتو مرتب کن. همین هم یه قدم خوبه.',
                'برای شروع، یکی از عکس‌هایی رو انتخاب کن که حس خوبی بهت می‌ده.',
                'امروز لازم نیست فنی فکر کنی؛ فقط بگو دوست داری این عکس چه حسی بده.',
                'یه آلبوم کوچیک بساز، مثلاً «کیوت»، «آینه‌ای»، «روزمره» یا «خاص».',
                'اگر شک داری چی بنویسی، من کمکت می‌کنم یه متن ساده و خوشگل بسازی.',
                'همه‌چیز قدم‌به‌قدمه؛ امروز فقط یک کار کوچیک انجام بده.',
                'اگه چیزی رو دوست نداری، راحت پاکش کن. کنترل همه‌چیز دست خودته.',
                'یه عکس انتخاب کن که با دیدنش لبخندت میاد؛ از همون شروع کنیم.',
            ])
        if not q:
            tips.extend([
                'یه آلبوم کوچولو بساز و اسم ساده بذار؛ مثلاً «کیوت»، «خاص» یا «امروز».',
                'اگه ذهنت خسته‌ست، فقط عکس‌ها رو دسته‌بندی کن. همینم کلی جلو بردنه.',
                'برای کپشن لازم نیست سخت بگیری؛ یه جمله کوتاه و واقعی خیلی قشنگ‌تره.',
            ])
            tips=list(dict.fromkeys(tips))
            random.shuffle(tips)
        return {'answer':'یه پیشنهاد کوچیک:\n'+'\n'.join('• '+t for t in tips[:3]),'sources':ctx,'mode':'rag'}

    def record_chat(self, tenant, user_text, assistant_text, sources, *, now_epoch_s):
        payload=json.dumps(sources or [], ensure_ascii=False)
        seed=f"{tenant}|{now_epoch_s}|{user_text}|{assistant_text}"
        tid=hashlib.sha256(seed.encode()).hexdigest()[:32]
        self._conn.execute("INSERT OR REPLACE INTO assistant_chat_turns VALUES (?,?,?,?,?,?)",(tid,tenant,str(user_text or "")[:800],str(assistant_text or "")[:4000],payload,int(now_epoch_s)))
        self._conn.commit()
        body=("کاربر: "+str(user_text or "")+"\nدستیار: "+str(assistant_text or ""))
        self.ingest_text(tenant, "chatbox", "چت باکس", body, now_epoch_s=now_epoch_s)
        return tid
    def chat_history(self, tenant, *, limit=20):
        rows=list(self._conn.execute("SELECT turn_id,user_text,assistant_text,sources_json,created_at FROM assistant_chat_turns WHERE tenant_id=? ORDER BY created_at DESC LIMIT ?",(tenant,int(limit))))
        out=[]
        for r in reversed(rows):
            try: src=json.loads(r["sources_json"] or "[]")
            except Exception: src=[]
            out.append({"id":r["turn_id"],"user":r["user_text"],"assistant":r["assistant_text"],"sources":src,"created_at":int(r["created_at"])})
        return out
    def record_run(self, tenant, source, status, detail, *, now_epoch_s):
        rid=hashlib.sha256((tenant+'|'+source+'|'+str(now_epoch_s)).encode()).hexdigest()[:32]
        self._conn.execute('INSERT OR REPLACE INTO assistant_runs VALUES (?,?,?,?,?,?)',
            (rid,tenant,source,status,str(detail or '')[:500],int(now_epoch_s)))
        self._conn.commit(); return rid
    def summary(self, tenant):
        n=self._conn.execute('SELECT COUNT(*) FROM assistant_chunks WHERE tenant_id=?',(tenant,)).fetchone()[0]
        r=self._conn.execute('SELECT status,detail,created_at FROM assistant_runs WHERE tenant_id=? ORDER BY created_at DESC LIMIT 1',(tenant,)).fetchone()
        return {'chunks':int(n),'last_run':dict(r) if r else None}
