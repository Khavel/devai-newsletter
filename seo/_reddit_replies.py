"""Fetch replies under our own comments via authenticated session."""
import json, sys, time
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from reddit_session import sync_playwright, PROFILE_DIR

# (sub, post_id, our_comment_fullname)
TARGETS = [
    ("Python", "1tromoz", "t1_ooq7x2h"),
    ("microsaas", "1tq1u0h", "t1_ooj7bou"),
    ("ClaudeAI", "1tsp83h", "t1_oowqiub"),
    ("microsaas", "1tsgpi1", "t1_oowqplu"),
    ("Python", "1ts5bgw", "t1_oowqwqq"),
]
OUT = Path(__file__).parent / ".reddit-replies-out.json"


def page_fetch_json(page, url):
    return page.evaluate("""(url) => fetch(url, {credentials:'same-origin', headers:{'Accept':'application/json'}}).then(r=>r.json()).then(d=>({ok:true,data:d})).catch(e=>({ok:false,error:e.message}))""", url)


def find_comment(children, target):
    for c in children:
        if c.get("kind") != "t1":
            continue
        d = c["data"]
        if d.get("name") == target:
            return d
        reps = d.get("replies")
        if reps and isinstance(reps, dict):
            r = find_comment(reps["data"]["children"], target)
            if r:
                return r
    return None


def flatten_replies(d, depth=0):
    out = []
    reps = d.get("replies")
    if reps and isinstance(reps, dict):
        for ch in reps["data"]["children"]:
            if ch.get("kind") != "t1":
                continue
            cd = ch["data"]
            out.append({
                "depth": depth,
                "author": cd.get("author"),
                "score": cd.get("score"),
                "name": cd.get("name"),
                "body": cd.get("body"),
                "is_op": cd.get("is_submitter"),
            })
            out.extend(flatten_replies(cd, depth + 1))
    return out


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
        for sub, pid, cid in TARGETS:
            res = page_fetch_json(page, f"https://old.reddit.com/r/{sub}/comments/{pid}.json?limit=300&raw_json=1")
            entry = {"sub": sub, "post_id": pid, "cid": cid}
            try:
                children = res["data"][1]["data"]["children"]
                mine = find_comment(children, cid)
                if mine:
                    entry["our_score"] = mine.get("score")
                    entry["replies"] = flatten_replies(mine)
                else:
                    entry["error"] = "our comment not found"
            except Exception as e:
                entry["error"] = str(e)
            out[cid] = entry
            time.sleep(1.5)
        ctx.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}\n")
    for cid, e in out.items():
        print(f"=== {e['sub']} {cid} (our score {e.get('our_score')}) ===")
        if e.get("error"):
            print("  ERR:", e["error"]); continue
        if not e.get("replies"):
            print("  (no replies)")
        for r in e["replies"]:
            tag = " [OP]" if r["is_op"] else ""
            print(f"  {'  '*r['depth']}[{r['score']}] {r['author']}{tag}: {r['body']}")
        print()


if __name__ == "__main__":
    main()
