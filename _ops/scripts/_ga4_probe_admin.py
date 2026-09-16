from pathlib import Path
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.analytics.admin_v1beta import AnalyticsAdminServiceClient
from google.analytics.admin_v1beta.types import Property, DataStream
from google.api_core import exceptions as gexc

token_path = Path(r"F:/backup/_ops/secrets/google-ga4/token.json")
creds = Credentials.from_authorized_user_file(str(token_path))
print("scopes", list(creds.scopes or []))
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
    token_path.write_text(creds.to_json(), encoding="utf-8")
client = AnalyticsAdminServiceClient(credentials=creds)
print("accounts:")
accts = []
try:
    for a in client.list_accounts():
        accts.append(a)
        print(" ", a.name, "|", a.display_name)
except Exception as e:
    print("list_accounts_fail", type(e).__name__, str(e)[:300])
print("summaries:")
try:
    for s in client.list_account_summaries():
        print(" ", s.account, "|", s.display_name, "props", len(list(s.property_summaries)))
except Exception as e:
    print("summaries_fail", type(e).__name__, str(e)[:300])
