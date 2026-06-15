"""Pull GSC error signals (sitemap status + URL inspection of homepage) for all
sites. Reconstructs what Search Console *email alerts* are warning about, since
the message center itself isn't in the API. Read-only.
"""
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
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
# Homepage to inspect per site (sc-domain has no scheme, supply https://)
HOMES = {
    "https://devaisemanal.com/": "https://devaisemanal.com/",
    "https://nbaproplab.com/": "https://nbaproplab.com/",
    "https://futpicks.com/": "https://futpicks.com/",
    "sc-domain:sharpyard.dev": "https://sharpyard.dev/",
}


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
            print(f"refresh failed ({e}); opening browser for re-consent…", flush=True)
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT), SCOPES)
    c = flow.run_local_server(port=0, prompt="consent",
                              success_message="GSC auth complete — cierra esta pestaña.")
    TOKEN.write_text(c.to_json())
    return c


def main():
    c = creds()
    enc = lambda s: s.replace('/', '%2F').replace(':', '%3A')
    for site in SITES:
        print(f"\n{'='*60}\n## {site}")
        # --- Sitemaps ---
        r = httpx.get(
            f"https://www.googleapis.com/webmasters/v3/sites/{enc(site)}/sitemaps",
            headers={"Authorization": f"Bearer {c.token}"}, timeout=40)
        if r.status_code != 200:
            print(f"  sitemaps: HTTP {r.status_code} {r.text[:160]}")
        else:
            sms = r.json().get("sitemap", [])
            if not sms:
                print("  sitemaps: (none submitted)")
            for s in sms:
                errs = int(s.get("errors", 0)); warns = int(s.get("warnings", 0))
                flag = "  ⚠️ ERRORS" if errs else ("  ⚠️ warnings" if warns else "  ok")
                print(f"  sitemap {s.get('path')}")
                print(f"    lastDownloaded={s.get('lastDownloaded','never')} "
                      f"errors={errs} warnings={warns} pending={s.get('isPending')}{flag}")
                for ci in s.get("contents", []):
                    print(f"      {ci.get('type')}: submitted={ci.get('submitted')} indexed={ci.get('indexed')}")
        # --- URL inspection of homepage ---
        home = HOMES[site]
        ir = httpx.post(
            "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect",
            headers={"Authorization": f"Bearer {c.token}", "Content-Type": "application/json"},
            json={"inspectionUrl": home, "siteUrl": site}, timeout=40)
        if ir.status_code != 200:
            print(f"  inspect {home}: HTTP {ir.status_code} {ir.text[:200]}")
        else:
            idx = ir.json().get("inspectionResult", {}).get("indexStatusResult", {})
            print(f"  inspect {home}:")
            print(f"    verdict={idx.get('verdict')} coverage={idx.get('coverageState')}")
            print(f"    robots={idx.get('robotsTxtState')} indexing={idx.get('indexingState')} "
                  f"fetch={idx.get('pageFetchState')}")
            if idx.get("lastCrawlTime"):
                print(f"    lastCrawl={idx.get('lastCrawlTime')}")


if __name__ == "__main__":
    main()
