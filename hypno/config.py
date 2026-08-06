from dataclasses import dataclass
import os,secrets

def _int(n,d):
    try:return int(os.environ.get(n,'') or d)
    except ValueError:return d
@dataclass(frozen=True)
class Config:
    root:str; host:str; port:int; state_dir:str; research_dir:str; bot_token:str; owners:tuple; api_key:str; base_url:str; model:str; dev_user:str
    @property
    def db_path(self): return os.path.join(self.state_dir,'hypno.sqlite')
    @property
    def web_root(self): return os.path.join(self.root,'web')
def load():
    root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    home=os.path.expanduser('~')
    owners=tuple(x.strip() for x in os.environ.get('HFM_OWNER_USER_IDS','').split(',') if x.strip())
    return Config(root,os.environ.get('HFM_HOST','127.0.0.1'),_int('HFM_PORT',8895),os.environ.get('HFM_STATE_DIR') or os.path.join(home,'.local','share','hypno-fugu-mini'),os.environ.get('HFM_RESEARCH_DIR') or os.path.join(root,'data','research'),os.environ.get('HFM_BOT_TOKEN',''),owners,os.environ.get('HFM_REMOTE_API_KEY',''),os.environ.get('HFM_REMOTE_BASE_URL','https://api.openai.com/v1'),os.environ.get('HFM_REMOTE_MODEL','fugu'),os.environ.get('HFM_DEV_USER_ID','ari-local'))
