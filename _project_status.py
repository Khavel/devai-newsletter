"""Pull GSC performance data for both sites to review project evolution."""
import sys, json, urllib.parse
sys.stdout.reconfigure(encoding="utf-8")
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / ".env", override=True)
from src.seo_intelligence import get_gsc_access_token
import httpx

token = get_gsc_access_token()
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
API = "https://www.googleapis.com/webmasters/v3/sites"

for site_url in ["https://devaisemanal.com/", "sc-domain:tpv-top.com"]:
    label = "devaisemanal.com" if "devai" in site_url else "tpv-top.com"
    print(f"\n{'='*60}")
    print(f" {label} — Performance Overview")
    print(f"{'='*60}")

    encoded = urllib.parse.quote(site_url, safe="")

    # Last 30 days
    body30 = {"startDate": "2026-04-21", "endDate": "2026-05-21", "dimensions": [], "type": "web"}
    r30 = httpx.post(f"{API}/{encoded}/searchAnalytics/query", headers=headers, json=body30)
    d30 = r30.json()

    # Previous 30 days
    body_prev = {"startDate": "2026-03-22", "endDate": "2026-04-21", "dimensions": [], "type": "web"}
    r_prev = httpx.post(f"{API}/{encoded}/searchAnalytics/query", headers=headers, json=body_prev)
    d_prev = r_prev.json()

    if "rows" in d30:
        row = d30["rows"][0]
        clicks = row["clicks"]
        impressions = row["impressions"]
        ctr = row["ctr"] * 100
        position = row["position"]
        print(f"  Last 30 days:")
        print(f"    Clicks:       {clicks}")
        print(f"    Impressions:  {impressions}")
        print(f"    CTR:          {ctr:.1f}%")
        print(f"    Avg Position: {position:.1f}")
    else:
        print("  Last 30 days: No data")

    if "rows" in d_prev:
        row_p = d_prev["rows"][0]
        clicks_p = row_p["clicks"]
        impressions_p = row_p["impressions"]
        ctr_p = row_p["ctr"] * 100
        position_p = row_p["position"]
        print(f"  Previous 30 days:")
        print(f"    Clicks:       {clicks_p}")
        print(f"    Impressions:  {impressions_p}")
        print(f"    CTR:          {ctr_p:.1f}%")
        print(f"    Avg Position: {position_p:.1f}")

        if "rows" in d30:
            c_delta = ((clicks - clicks_p) / max(clicks_p, 1)) * 100
            i_delta = ((impressions - impressions_p) / max(impressions_p, 1)) * 100
            print(f"  Growth:")
            print(f"    Clicks:       {c_delta:+.0f}%")
            print(f"    Impressions:  {i_delta:+.0f}%")
    else:
        print("  Previous 30 days: No data (site is new)")

    # Top queries
    body_q = {"startDate": "2026-04-21", "endDate": "2026-05-21", "dimensions": ["query"], "rowLimit": 10, "type": "web"}
    rq = httpx.post(f"{API}/{encoded}/searchAnalytics/query", headers=headers, json=body_q)
    dq = rq.json()

    if "rows" in dq:
        print(f"\n  Top 10 queries (last 30d):")
        for row in dq["rows"]:
            q = row["keys"][0][:50]
            c = row["clicks"]
            i = row["impressions"]
            ct = row["ctr"] * 100
            p = row["position"]
            print(f"    {q:<50}  clk={c:<4} imp={i:<6} ctr={ct:.1f}%  pos={p:.1f}")

    # Top pages
    body_p = {"startDate": "2026-04-21", "endDate": "2026-05-21", "dimensions": ["page"], "rowLimit": 10, "type": "web"}
    rp = httpx.post(f"{API}/{encoded}/searchAnalytics/query", headers=headers, json=body_p)
    dp = rp.json()

    if "rows" in dp:
        print(f"\n  Top 10 pages (last 30d):")
        for row in dp["rows"]:
            pg = row["keys"][0].replace("https://devaisemanal.com", "").replace("https://tpv-top.com", "")[:55]
            c = row["clicks"]
            i = row["impressions"]
            print(f"    {pg:<55}  clk={c:<4} imp={i:<6}")

    # Weekly breakdown (last 4 weeks)
    print(f"\n  Weekly trend:")
    weeks = [
        ("2026-04-21", "2026-04-27", "W1 Apr21-27"),
        ("2026-04-28", "2026-05-04", "W2 Apr28-May04"),
        ("2026-05-05", "2026-05-11", "W3 May05-11"),
        ("2026-05-12", "2026-05-18", "W4 May12-18"),
    ]
    for start, end, wlabel in weeks:
        bw = {"startDate": start, "endDate": end, "dimensions": [], "type": "web"}
        rw = httpx.post(f"{API}/{encoded}/searchAnalytics/query", headers=headers, json=bw)
        dw = rw.json()
        if "rows" in dw:
            r = dw["rows"][0]
            print(f"    {wlabel:<18}  clk={r['clicks']:<4} imp={r['impressions']:<6} ctr={r['ctr']*100:.1f}%  pos={r['position']:.1f}")
        else:
            print(f"    {wlabel:<18}  No data")

print("\n")
