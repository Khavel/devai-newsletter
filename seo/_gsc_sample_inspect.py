"""Sample-inspect interior URLs from futpicks + devaisemanal sitemaps to find
which pages Search Console is excluding (the 'Page indexing issues' email).
Read-only; uses cached token (now valid)."""
import sys, re, random
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
import httpx
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

ROOT = Path(__file__).resolve().parent.parent
SCOPES = ["https://www.googleapis.com/auth/webmasters"]
TOKEN = ROOT / "token-webmasters.json"

# (siteUrl for inspection API, sitemap url, sample size)
TARGETS = [
    ("https://futpicks.com/", "https://futpicks.com/api/v1/seo/sitemap.xml", 12),
    ("https://futpicks.com/", "https://futpicks.com/sitemap.xml", 8),
    ("https://devaisemanal.com/", "https://devaisemanal.com/sitemap.xml", 15),
]


def creds():
    c = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if not c.valid and c.expired and c.refresh_token:
        c.refresh(Request()); TOKEN.write_text(c.to_json())
    return c


def urls_from_sitemap(url):
    r = httpx.get(url, timeout=40, follow_redirects=True)
    locs = re.findall(r"<loc>\s*([^<]+?)\s*</loc>", r.text)
    # drop image locs / nested sitemaps that aren't page urls
    return [u for u in locs if not u.endswith(".xml")]


def inspect(token, site, url):
    r = httpx.post(
        "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"inspectionUrl": url, "siteUrl": site}, timeout=40)
    if r.status_code != 200:
        return {"_http": f"{r.status_code} {r.text[:120]}"}
    return r.json().get("inspectionResult", {}).get("indexStatusResult", {})


def main():
    c = creds()
    random.seed(7)
    for site, sm, n in TARGETS:
        print(f"\n{'='*64}\n## sitemap {sm}")
        urls = urls_from_sitemap(sm)
        print(f"  {len(urls)} page URLs found; inspecting sample of {min(n,len(urls))}")
        sample = urls if len(urls) <= n else random.sample(urls, n)
        buckets = {}
        for u in sample:
            idx = inspect(c.token, site, u)
            cov = idx.get("coverageState", idx.get("_http", "?"))
            buckets.setdefault(cov, []).append(u)
        for cov, us in sorted(buckets.items(), key=lambda kv: -len(kv[1])):
            print(f"\n  [{len(us)}] {cov}")
            for u in us[:6]:
                print(f"      {u}")
            if len(us) > 6:
                print(f"      … +{len(us)-6} more")


if __name__ == "__main__":
    main()
