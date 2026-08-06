import json
from hypno.config import load
from hypno.adapters.store import Store
cfg=load(); st=Store(cfg.db_path)
with st.conn() as db:
    db.execute("DELETE FROM research_docs WHERE source_url LIKE 'attachment://pasted_text_178593%'")
    db.execute("INSERT INTO research_fts(research_fts) VALUES('rebuild')")
count=0
for line in open('research_import/rag_import.jsonl',encoding='utf-8'):
    d=json.loads(line)
    text=f"[category: {d.get('category')}]\n[section: {d.get('section')}]\n[source: {d.get('source_url')}]\n\n{d.get('text','')}"
    tags=(d.get('tags','')+' '+d.get('category','')+' '+d.get('primary_category','')).strip()
    st.add_research(d['title'][:240], text, source_url=d.get('source_url',''), source_type='attachment_chunk', tags=tags)
    count+=1
print('imported_chunks',count)
print('research_count',st.count())
