from pathlib import Path
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
CLIENT = Path(r"F:\backup\_ops\secrets\google-ga4\oauth-client.json")
TOKEN = Path(r"F:\backup\_ops\secrets\google-ga4\token.json")
STATUS = Path(r"F:\backup\06-EVIDENCE\OCTOPUS-CG001-GA4-OAUTH-START-2026-08-23\CONSENT-STATUS.json")

def main():
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT), SCOPES)
    creds = flow.run_local_server(port=8765, open_browser=True, success_message="GA4 consent OK — close this tab.")
    TOKEN.parent.mkdir(parents=True, exist_ok=True)
    TOKEN.write_text(creds.to_json(), encoding="utf-8")
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(json.dumps({"ok": True, "has_refresh_token": bool(creds.refresh_token), "token_bytes": TOKEN.stat().st_size, "scopes": list(creds.scopes or SCOPES), "metrics_allowed": False}, indent=2) + "\n", encoding="utf-8")
    print("CONSENT_OK", bool(creds.refresh_token), TOKEN.stat().st_size)

if __name__ == "__main__":
    main()
