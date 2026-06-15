"""Focused 28-day GSC status for sharpyard + devaisemanal: totals, top queries,
top pages. Read-only; uses cached (now valid) token."""
import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from datetime import date, timedelta
import httpx
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

ROOT = Path(__file__).resolve().parent.parent
SCOPES = ["https://www.googleapis.com/auth/webmasters"]
TOKEN = ROOT / "token-webmasters.json"
SITES = ["sc-domain:sharpyard.dev", "https://devaisemanal.com/"]


def creds():
    c = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if not c.valid and c.expired and c.refresh_token:
        c.refresh(Request()); TOKEN.write_text(c.to_json())
    return c


def query(token, site, start, end, dims, limit):
    enc = site.replace('/', '%2F').replace(':', '%3A')
    r = httpx.post(
        f"https://www.googleapis.com/webmasters/v3/sites/{enc}/searchAnalytics/query",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"startDate": start, "endDate": end, "dimensions": dims, "rowLimit": limit},
        timeout=40)
    return r.json().get("rows", []) if r.status_code == 200 else [{"_err": f"{r.status_code} {r.text[:120]}"}]


def main():
    c = creds()
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=27)
    print(f"=== GSC 28-day  {start} → {end} ===")
    for site in SITES:
        tot = query(c.token, site, str(start), str(end), [], 1)
        print(f"\n{'#'*56}\n## {site}")
        if tot and "_err" in tot[0]:
            print(f"   ERROR {tot[0]['_err']}"); continue
        t = tot[0] if tot else {}
        print(f"   clicks={t.get('clicks',0):.0f}  impressions={t.get('impressions',0):.0f}  "
              f"ctr={100*t.get('ctr',0):.2f}%  avg_pos={t.get('position',0):.1f}")
        print("\n   ── top queries ──")
        for r in query(c.token, site, str(start), str(end), ["query"], 15):
            if "_err" in r: print(f"     {r['_err']}"); break
            print(f"     {r['keys'][0][:46]:46} clk={r['clicks']:>3.0f} imp={r['impressions']:>5.0f} "
                  f"ctr={100*r['ctr']:>5.1f}% pos={r['position']:>4.1f}")
        print("\n   ── top pages ──")
        for r in query(c.token, site, str(start), str(end), ["page"], 10):
            if "_err" in r: print(f"     {r['_err']}"); break
            pg = r['keys'][0].replace("https://","").replace("sharpyard.dev","").replace("devaisemanal.com","")
            print(f"     {pg[:46]:46} clk={r['clicks']:>3.0f} imp={r['impressions']:>5.0f} pos={r['position']:>4.1f}")


if __name__ == "__main__":
    main()
