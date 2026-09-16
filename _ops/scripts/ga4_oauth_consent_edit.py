from pathlib import Path
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/analytics.edit",
]
CLIENT = Path(r"F:\backup\_ops\secrets\google-ga4\oauth-client.json")
TOKEN = Path(r"F:\backup\_ops\secrets\google-ga4\token.json")
STATUS = Path(r"F:\backup\06-EVIDENCE\OCTOPUS-CG001-GA4-OAUTH-START-2026-08-23\CONSENT-EDIT-STATUS.json")

def main():
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT), SCOPES)
    creds = flow.run_local_server(port=8765, open_browser=True, success_message="Edit consent OK — close tab.")
    TOKEN.write_text(creds.to_json(), encoding="utf-8")
    STATUS.write_text(json.dumps({
        "ok": True,
        "has_refresh_token": bool(creds.refresh_token),
        "scopes": list(creds.scopes or SCOPES),
        "token_bytes": TOKEN.stat().st_size,
    }, indent=2) + "\n", encoding="utf-8")
    print("CONSENT_EDIT_OK", list(creds.scopes or []), TOKEN.stat().st_size)

if __name__ == "__main__":
    main()
