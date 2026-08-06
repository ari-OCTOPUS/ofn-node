SEEDS=[('NCCIH: Hypnosis overview','https://www.nccih.nih.gov/health/hypnosis','hypnosis evidence safety','Hypnosis is focused attention with guided relaxation or imagery. Evidence suggests it may help some painful conditions and selected clinical contexts. It should not replace standard medical care and self-hypnosis should be practiced in a safe place, not during activities requiring alertness.'),('APA 2024: Science of clinical hypnosis','https://www.apa.org/monitor/2024/04/science-of-hypnosis','clinical hypnosis pain anxiety sleep','Modern clinical hypnosis is an evidence-informed psychological tool involving focused attention and response to suggestion. It is not mind control; ethical hypnosis emphasizes consent, collaboration, and patient agency.'),('Safe self-hypnosis contract','local://safety','consent exit grounding','Safe self-hypnosis starts with consent, safe location, clear goal, reversible suggestions and an exit routine. Suggestions are phrased as choices, and the session ends with counting up, movement and orientation.')]

SAFE_TAGS=('hypnosis_core','self_love_training','safety_boundaries','neuroscience','math_models','philosophy_symbolism')
RELEVANT_TERMS=('هیپنوتیز','خودهیپنوتیز','تلقین','آرام','تمرکز','خواب','اضطراب','بدن','باشگاه','خوددوستی','تنفس','hypnosis','self-hypnosis','suggestion','trance','relaxation','focus','sleep','anxiety','safety','consent')
EXCLUDED_TERMS=('ماینینگ','mining','business','بیزنس','resource monopoly','تصاحب منابع','takeover','zero-day','exploit','bypass security','data infiltration','self-replicating','replicator agents','autonomous agi','protocol bypassing','api exploitation')

def seed(store,research_dir):
    import os
    os.makedirs(research_dir,exist_ok=True)
    if store.count(): return 0
    for t,u,tags,txt in SEEDS:
        store.add_research(t,txt,u,'seed',tags)
        
        with open(os.path.join(research_dir,t.replace(':','').replace(' ','-')+'.md'),'w',encoding='utf-8') as f:
            f.write(f'# {t}\nSource: {u}\n\n{txt}\n')
    return len(SEEDS)

def is_safe_research(title='', text='', tags='', source_url=''):
    blob=' '.join([str(title or ''),str(text or ''),str(tags or ''),str(source_url or '')]).lower()
    if any(x.lower() in blob for x in EXCLUDED_TERMS):
        return False
    return any(x.lower() in blob for x in RELEVANT_TERMS)

def retrieve(store,q,limit=5):
    rows=store.search(q,limit*4)
    out=[]
    for r in rows:
        if is_safe_research(r.get('title',''),r.get('text',''),r.get('tags',''),r.get('source_url','')):
            out.append(r)
        if len(out)>=limit: break
    return out

