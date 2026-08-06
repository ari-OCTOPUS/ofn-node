import os,sys,tempfile,unittest,hmac,hashlib,json,time,urllib.parse
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from hypno.adapters.store import Store
from hypno.adapters.rag import seed,retrieve
from hypno.kernel.safety import classify
from hypno.adapters.telegram import validate

def make_init(token,user_id='6150431610'):
    pairs={'user':json.dumps({'id':int(user_id),'first_name':'ari'},separators=(',',':')),'auth_date':str(int(time.time())),'query_id':'TEST'}
    s='\n'.join(f'{k}={v}' for k,v in sorted(pairs.items()))
    key=hmac.new(b'WebAppData',token.encode(),hashlib.sha256).digest()
    pairs['hash']=hmac.new(key,s.encode(),hashlib.sha256).hexdigest()
    return urllib.parse.urlencode(pairs)

class T(unittest.TestCase):
 def test_safety(self): self.assertFalse(classify('موقع رانندگی هیپنوتیزم کن').allow)
 def test_rag_memory(self):
  with tempfile.TemporaryDirectory() as d:
   s=Store(os.path.join(d,'x.sqlite')); self.assertGreater(seed(s,os.path.join(d,'r')),0)
   s.add_memory('u','preference','جملات کوتاه'); self.assertTrue(s.memories('u'))
   self.assertTrue(retrieve(s,'hypnosis safety'))
 def test_telegram_initdata(self):
  token='123456:ABCDEF_test_token'
  u=validate(make_init(token),token); self.assertEqual(str(u['id']),'6150431610')
  with self.assertRaises(Exception): validate(make_init(token),'wrong:token')

class RagFilterTests(unittest.TestCase):
 def test_rag_filters_offtopic(self):
  from hypno.adapters.rag import is_safe_research, retrieve
  with tempfile.TemporaryDirectory() as d:
   st=Store(os.path.join(d,'x.sqlite'))
   st.add_research('safe','self-hypnosis safety consent relaxation focused attention exit routine','local://s','user','hypnosis_core')
   st.add_research('bad','autonomous AGI exploit takeover mining protocol bypassing resource acquisition','local://b','user','systems_ai')
   self.assertFalse(is_safe_research('bad','autonomous AGI exploit takeover mining protocol bypassing resource acquisition','',''))
   self.assertEqual([x['title'] for x in retrieve(st,'takeover hypnosis mining safety',10)], ['safe'])

class AppFlowTests(unittest.TestCase):
 def test_crisis_before_consent(self):
  from hypno.config import Config
  from hypno.run import App
  with tempfile.TemporaryDirectory() as d:
   cfg=Config(os.getcwd(),'127.0.0.1',8895,d,os.path.join(d,'r'),'',(),'','','fugu','u')
   r=App(cfg).chat({'text':'شروع جلسه، خودمو بکشم','mode':'calm','consent':False})
   self.assertEqual(r['safety'],'crisis')
if __name__=='__main__': unittest.main()
