"""GA4 traffic reader — 28-day sessions/users/views by channel for devaisemanal
+ sharpyard. Re-consents with analytics.readonly (Data API needs it; the existing
.ga-oauth-token.json is analytics.edit only). Reuses the OAuth client from that
file. Writes a separate read-scoped token so ga_admin.py's edit token is untouched."""
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from datetime import date, timedelta
import httpx
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

HERE = Path(__file__).parent
EDIT_TOKEN = HERE / ".ga-oauth-token.json"          # existing (analytics.edit) — source of client id/secret
READ_TOKEN = HERE / ".ga-oauth-data-token.json"     # new (analytics.readonly) for Data API
SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
WANT_KEYS = {"devai", "semanal", "sharpyard"}


def creds():
    c = None
    if READ_TOKEN.exists():
        c = Credentials.from_authorized_user_file(str(READ_TOKEN), SCOPES)
    if c and c.valid:
        return c
    if c and c.expired and c.refresh_token:
        try:
            c.refresh(Request()); READ_TOKEN.write_text(c.to_json(), encoding="utf-8"); return c
        except Exception as e:
            print(f"refresh failed ({e}); opening browser for consent…", flush=True)
    src = json.loads(EDIT_TOKEN.read_text(encoding="utf-8"))
    client_config = {"installed": {
        "client_id": src["client_id"], "client_secret": src["client_secret"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": src.get("token_uri", "https://oauth2.googleapis.com/token"),
        "redirect_uris": ["http://localhost"]}}
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    c = flow.run_local_server(port=0, prompt="consent",
                              success_message="GA4 auth complete — cierra esta pestaña.")
    READ_TOKEN.write_text(c.to_json(), encoding="utf-8")
    return c


def norm(d):
    return d.lower().replace("https://", "").replace("http://", "").rstrip("/").removeprefix("www.")


def main():
    c = creds()
    H = {"Authorization": f"Bearer {c.token}"}
    # 1) account summaries → property ids + their stream URIs
    r = httpx.get("https://analyticsadmin.googleapis.com/v1beta/accountSummaries",
                  headers=H, params={"pageSize": 200}, timeout=40)
    if r.status_code != 200:
        print(f"accountSummaries HTTP {r.status_code}: {r.text[:200]}"); return
    props = {}  # property_id -> display_name
    for acc in r.json().get("accountSummaries", []):
        for p in acc.get("propertySummaries", []):
            pid = p["property"].split("/")[-1]
            props[pid] = p.get("displayName", "")
    # match by display name to our domains (best-effort)
    targets = {pid: name for pid, name in props.items()
               if any(w in name.lower() for w in WANT_KEYS)}
    print("matched properties:", targets or "(none — listing all)")
    if not targets:
        targets = props

    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=27)
    for pid, name in targets.items():
        print(f"\n{'#'*56}\n## {name}  (property {pid})   {start} → {end}")
        body = {
            "dateRanges": [{"startDate": str(start), "endDate": str(end)}],
            "dimensions": [{"name": "sessionDefaultChannelGroup"}],
            "metrics": [{"name": "sessions"}, {"name": "totalUsers"},
                        {"name": "screenPageViews"}, {"name": "engagementRate"}],
            "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}],
        }
        rr = httpx.post(f"https://analyticsdata.googleapis.com/v1beta/properties/{pid}:runReport",
                        headers=H, json=body, timeout=60)
        if rr.status_code != 200:
            print(f"   runReport HTTP {rr.status_code}: {rr.text[:200]}"); continue
        data = rr.json()
        rows = data.get("rows", [])
        tot = data.get("totals", [{}])
        if not rows:
            print("   (no traffic in window)"); continue
        ts = tot[0]["metricValues"] if tot and tot[0].get("metricValues") else []
        if ts:
            print(f"   TOTAL sessions={ts[0]['value']} users={ts[1]['value']} "
                  f"views={ts[2]['value']}")
        print("   ── by channel ──")
        for row in rows:
            ch = row["dimensionValues"][0]["value"]
            m = row["metricValues"]
            print(f"     {ch[:24]:24} sess={m[0]['value']:>4} users={m[1]['value']:>4} "
                  f"views={m[2]['value']:>5} eng={float(m[3]['value'])*100:.0f}%")


if __name__ == "__main__":
    main()
