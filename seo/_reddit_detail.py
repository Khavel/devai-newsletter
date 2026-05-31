"""Fetch top-level comments for specific posts via authenticated session."""
import json, sys, time
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from reddit_session import sync_playwright, PROFILE_DIR

TARGETS = [
    ("ClaudeAI", "1tsp83h"),
    ("microsaas", "1tsgpi1"),
    ("Python", "1ts5bgw"),
]
OUT = Path(__file__).parent / ".reddit-detail-out.json"


def page_fetch_json(page, url):
    return page.evaluate("""(url) => fetch(url, {credentials:'same-origin', headers:{'Accept':'application/json'}}).then(r=>r.json()).then(d=>({ok:true,data:d})).catch(e=>({ok:false,error:e.message}))""", url)


def main():
    out = {}
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            PROFILE_DIR, headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-first-run"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://old.reddit.com/", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        for sub, pid in TARGETS:
            res = page_fetch_json(page, f"https://old.reddit.com/r/{sub}/comments/{pid}.json?limit=30&sort=top&raw_json=1")
            comments = []
            try:
                for ch in res["data"][1]["data"]["children"]:
                    if ch.get("kind") != "t1":
                        continue
                    cd = ch["data"]
                    comments.append({"author": cd.get("author"), "score": cd.get("score"), "body": (cd.get("body") or "")[:600]})
            except Exception as e:
                comments.append({"error": str(e)})
            out[pid] = comments
            time.sleep(1.5)
        ctx.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")
    for pid, cs in out.items():
        print(f"\n=== {pid} ({len(cs)} top comments) ===")
        for c in cs[:8]:
            if "error" in c:
                print("  ERR", c["error"]); continue
            print(f"  [{c['score']}] {c['author']}: {c['body'][:200]}")


if __name__ == "__main__":
    main()
