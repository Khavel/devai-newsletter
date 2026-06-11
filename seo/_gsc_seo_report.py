"""Re-auth Search Console (token expired/revoked) and pull a 28-day SEO snapshot
for all 3 sites. Opens a browser for consent on first run; caches to
../token-webmasters.json. Read-only use of the webmasters scope.
"""
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from datetime import date, timedelta
import httpx
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

ROOT = Path(__file__).resolve().parent.parent
SCOPES = ["https://www.googleapis.com/auth/webmasters"]
TOKEN = ROOT / "token-webmasters.json"
CLIENT = ROOT / "gsc-oauth-client.json"
SITES = ["https://devaisemanal.com/", "https://nbaproplab.com/", "https://futpicks.com/",
         "sc-domain:sharpyard.dev"]


def creds():
    c = None
    if TOKEN.exists():
        c = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if c and c.valid:
        return c
    if c and c.expired and c.refresh_token:
        try:
            c.refresh(Request()); TOKEN.write_text(c.to_json()); return c
        except Exception as e:
            print(f"refresh failed ({e}); re-consenting…")
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT), SCOPES)
    c = flow.run_local_server(port=0, prompt="consent",
                              success_message="GSC auth complete — cierra esta pestaña.")
    TOKEN.write_text(c.to_json())
    return c


def query(token, site, start, end, dims, limit=10):
    r = httpx.post(
        f"https://www.googleapis.com/webmasters/v3/sites/{httpx.URL(site)}/searchAnalytics/query".replace(
            str(httpx.URL(site)), site.replace('/', '%2F')),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"startDate": start, "endDate": end, "dimensions": dims, "rowLimit": limit},
        timeout=40)
    return r


def main():
    c = creds()
    print("auth OK\n")
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=27)
    print(f"=== Search Console — {start} to {end} (28d) ===")
    for site in SITES:
        # totals
        rt = query(c.token, site, str(start), str(end), [])
        tot = rt.json().get("rows", [{}]) if rt.status_code == 200 else []
        if rt.status_code != 200:
            print(f"\n## {site}  HTTP {rt.status_code}: {rt.text[:160]}")
            continue
        t = tot[0] if tot else {}
        print(f"\n## {site}")
        print(f"   clicks={t.get('clicks',0):.0f}  impressions={t.get('impressions',0):.0f}  "
              f"ctr={100*t.get('ctr',0):.2f}%  avg_pos={t.get('position',0):.1f}")
        rq = query(c.token, site, str(start), str(end), ["query"], 5)
        for row in (rq.json().get("rows", []) if rq.status_code == 200 else []):
            q = row["keys"][0]
            print(f"     • {q[:42]:42} clk={row['clicks']:.0f} imp={row['impressions']:.0f} pos={row['position']:.1f}")


if __name__ == "__main__":
    main()
