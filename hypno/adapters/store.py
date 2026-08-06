import os,sqlite3,time,json
SCHEMA='''PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL;
CREATE TABLE IF NOT EXISTS memories(id INTEGER PRIMARY KEY,user_id TEXT,kind TEXT,content TEXT,created_at INT,active INT DEFAULT 1);
CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY,user_id TEXT,role TEXT,content TEXT,meta TEXT,created_at INT);
CREATE TABLE IF NOT EXISTS research_docs(id INTEGER PRIMARY KEY,title TEXT,source_url TEXT,source_type TEXT,text TEXT,tags TEXT,created_at INT);
CREATE VIRTUAL TABLE IF NOT EXISTS research_fts USING fts5(title,text,tags,content='research_docs',content_rowid='id');
CREATE TRIGGER IF NOT EXISTS research_ai AFTER INSERT ON research_docs BEGIN INSERT INTO research_fts(rowid,title,text,tags) VALUES(new.id,new.title,new.text,new.tags); END;
CREATE TABLE IF NOT EXISTS sessions(user_id TEXT PRIMARY KEY,mode TEXT DEFAULT 'calm',consent INT DEFAULT 0,last_seen INT);
CREATE TABLE IF NOT EXISTS edge_daily(
  id INTEGER PRIMARY KEY,
  user_id TEXT NOT NULL,
  day TEXT NOT NULL,
  b REAL, c REAL, x REAL,
  verdict TEXT,
  created_at INT NOT NULL,
  UNIQUE(user_id, day)
);'''
class Store:
    def __init__(self,path):
        self.path=path; os.makedirs(os.path.dirname(path),exist_ok=True)
        with self.conn() as db: db.executescript(SCHEMA)
    def conn(self): c=sqlite3.connect(self.path,timeout=20); c.row_factory=sqlite3.Row; return c
    def now(self): return int(time.time())
    def session(self,user,mode=None,consent=None):
        n=self.now()
        with self.conn() as db:
            db.execute("INSERT OR IGNORE INTO sessions(user_id,last_seen) VALUES(?,?)",(user,n))
            if mode is not None: db.execute("UPDATE sessions SET mode=?,last_seen=? WHERE user_id=?",(mode,n,user))
            if consent is not None: db.execute("UPDATE sessions SET consent=?,last_seen=? WHERE user_id=?",(1 if consent else 0,n,user))
            return dict(db.execute("SELECT * FROM sessions WHERE user_id=?",(user,)).fetchone())
    def add_memory(self,user,kind,content):
        if not content.strip(): raise ValueError('empty memory')
        n=self.now()
        with self.conn() as db: return db.execute("INSERT INTO memories(user_id,kind,content,created_at) VALUES(?,?,?,?)",(user,kind or 'note',content.strip()[:2000],n)).lastrowid
    def memories(self,user,limit=8):
        with self.conn() as db: rows=db.execute("SELECT kind,content FROM memories WHERE user_id=? AND active=1 ORDER BY created_at DESC LIMIT ?",(user,limit)).fetchall()
        return [f"{r['kind']}: {r['content']}" for r in rows]
    def log(self,user,role,content,meta=None):
        with self.conn() as db: db.execute("INSERT INTO messages(user_id,role,content,meta,created_at) VALUES(?,?,?,?,?)",(user,role,content,json.dumps(meta or {},ensure_ascii=False),self.now()))
    def add_research(self,title,text,source_url='',source_type='manual',tags=''):
        if len((text or '').strip())<40: raise ValueError('research text too short')
        with self.conn() as db: return db.execute("INSERT INTO research_docs(title,source_url,source_type,text,tags,created_at) VALUES(?,?,?,?,?,?)",((title or 'Untitled')[:240],source_url,source_type,text.strip(),tags,self.now())).lastrowid
    def count(self):
        with self.conn() as db: return db.execute('SELECT COUNT(*) FROM research_docs').fetchone()[0]
    def search(self,q,limit=5):
        toks=[x.replace('"','') for x in (q or '').split() if len(x)>1][:10]
        if not toks: return []
        expr=' OR '.join('"%s"'%x for x in toks)
        with self.conn() as db:
            try: rows=db.execute("SELECT d.id,d.title,d.source_url,d.tags,snippet(research_fts,1,'','','…',32) text FROM research_fts JOIN research_docs d ON d.id=research_fts.rowid WHERE research_fts MATCH ? LIMIT ?",(expr,limit)).fetchall()
            except sqlite3.OperationalError: rows=[]
        return [dict(r) for r in rows]

    def _today_utc(self):
        import datetime as _dt
        return _dt.datetime.now(_dt.timezone.utc).strftime('%Y-%m-%d')

    def log_edge_daily(self, user, b, c, x, verdict, day=None):
        """یک نمرهٔ روزانهٔ لبه را ذخیره کن (upsert: یک ردیف در هر روز)."""
        day = day or self._today_utc()
        n = self.now()
        with self.conn() as db:
            db.execute(
                "INSERT INTO edge_daily(user_id,day,b,c,x,verdict,created_at) "
                "VALUES(?,?,?,?,?,?,?) "
                "ON CONFLICT(user_id,day) DO UPDATE SET "
                "b=excluded.b,c=excluded.c,x=excluded.x,verdict=excluded.verdict,created_at=excluded.created_at",
                (user, day, float(b), float(c), float(x), str(verdict), n),
            )
            return day

    def edge_history(self, user, limit=14):
        """آخرین N روز لبه را به ترتیب قدیم‌به‌جدید برگردان."""
        with self.conn() as db:
            rows = db.execute(
                "SELECT day,b,c,x,verdict FROM edge_daily WHERE user_id=? "
                "ORDER BY day DESC LIMIT ?",
                (user, int(limit)),
            ).fetchall()
        return [dict(r) for r in reversed(rows)]
