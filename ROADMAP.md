# Promotion & Growth Roadmap

> **Products:** DevAI Semanal · NbaPropLab · FutPicks
> **Last updated:** 2026-05-30

---

## What's Been Done

### Twitter/X Infrastructure (All 3 Products) ✅
- Developer account on X Platform (pay-per-use, App ID: 32989211), $25 credits loaded
- @FutProbLab → OAuth 1.0a; @DevAISemanal + @StatLineNerd → OAuth 2.0 PKCE
- Posting script `seo/twitter_api_post.py` (all 3 accounts, both auth methods) + `seo/oauth2_exchange.py`
- Chrome browser automation fallback (all 3 accounts logged in, account switching)
- Scheduled: daily posting (3 PM CET) + engagement (5 PM CET)
- ISO 8601 timestamped logs, 7-10 min inter-account gap enforced
- **Image/media attachment built (2026-05-30):** `--pick-id` / `--image-url` / `--image` flags. OAuth2 → X v2 `media/upload`; OAuth1 → v1.1. @StatLineNerd re-authorized with the `media.write` scope. Verified end-to-end.
- **Detailed docs:** [`seo/CLAUDE.md`](seo/CLAUDE.md)

### Twitter Live-Data Integration (NBA/WNBA + Football) ✅ NEW
The daily routine now posts **real model data**, not just generic content.
- **NBA/WNBA → `proplab` MCP** (replaces the dead `nba-edge` MCP). Public tools (`proplab_dashboard`, `proplab_track_record`, `proplab_pick_details`, `proplab_games`) need no auth. Covers both leagues — **@StatLineNerd is now effectively year-round** (WNBA summer, NBA fall–spring).
- **Football → `footballlab` MCP** (built but unregistered; registered in `.claude.json` 2026-05-30, boots + 17 tools verified). Public `flab_*` tools cover picks/matches/track-record. Base domain: **futpicks.com**.
- **Real schemas captured:** `seo/API_SCHEMAS_NBA.md`, `seo/API_SCHEMAS_FUTPICKS.md` (the OpenAPI docs omit response bodies).
- **MCP-first integration plans:** `seo/API_INTEGRATION_PLAN_NBA.md`, `seo/API_INTEGRATION_PLAN_FUTPICKS.md`.
- **SKILL updated** for both MCPs, WNBA handling, edge-vs-score filtering, bilingual football (summary_es/_en).
- **Live posts verified** on @StatLineNerd (NBA/WNBA picks + results) and @FutProbLab (ROI track record).

### Pick Card Images (NbaPropLab) ✅ NEW
- Public per-pick card endpoint: `https://nbaproplab.com/api/v1/screenshots/pick/{id}.png` (1200×675, the OG image).
- **Render bug fixed** (radar was blank) + **card redesigned** (labeled/filled radar, "WHY IT SCORES" factor bars, reason line, score ring) — now communicates value to a cold viewer. (Both fixed in the `NBAv3-fresh` repo via spawned tasks.)
- Attachable to tweets via `--pick-id` (headless, API v2). First image tweet posted 2026-05-30.

### Directory Submissions (DevAI Semanal) ✅
- **Live:** Product Hunt (launched), Crunchbase, Paved, InboxReads, LetterList, Rad Letters, StackLetter
- **GitHub PRs (5 repos):** awesome-newsletters, awesome-ai-newsletters, awesome-weekly, developer-newsletters, awesome-web-newsletters (DA 96 each)
- Dev.to article + Ghost canonical page live; 19 spam domains disavowed in GSC
- **Detailed docs:** [`seo/directory-submissions.md`](seo/directory-submissions.md)

### Reddit Warm-Up (DevAI Semanal) ✅ In Progress
- Account Khavel_dev (created 2026-05-26); `seo/reddit_post_comment.py` (old.reddit.com API via Playwright)
- Phase 1 daily value comments on r/ClaudeAI, r/microsaas, r/SideProject, r/SaaS (Phase 2 gate: June 25)

### Cross-Posting (DevAI Semanal) ✅ — 4 platforms
- **Medium** (medium.com/@khavel), **Hashnode** (devaisemanal.hashnode.dev), **Dev.to** (dev.to/khavel) — all canonical → devaisemanal.com
- **Substack** (khavel.substack.com) — no canonical override (self-canonicalizes); DA 93 backlink via in-body attribution link
- Author: **Khavel** on all. 1st article (newsletter automation) live on all 4. 2nd article (value betting) on Dev.to/Medium/Substack; Hashnode auto-archived it (betting topic).
- **Detailed docs:** [`seo/CLAUDE.md`](seo/CLAUDE.md) · log: `seo/crosspost_log.jsonl`

### Product Docs / Infra (FutPicks) ✅
- **Scalar interactive API docs** live in prod at `https://futpicks.com/api/v1/scalar/v1` (fixed: proxied path + `.AllowAnonymous()` past the `FallbackPolicy`). OpenAPI spec at `/api/v1/openapi/v1.json`.

---

## What's Left

### Image Tweets — remaining
- [ ] **@FutProbLab cards** — OAuth1 media upload is built (no re-auth needed), but the football card endpoint `futpicks.com/api/v1/screenshots/pick/{id}.png` is **401-gated** (same `FallbackPolicy` as Scalar). Needs `.AllowAnonymous()` on the screenshots + og endpoints, then football cards work immediately.
- [ ] **@DevAISemanal images** — would need its own `media.write` re-auth (`oauth2_exchange.py`) if images are ever wanted there.

### Pending Directory Submissions (DevAI Semanal)
| Directory | Blocker | Action |
|-----------|---------|--------|
| **G2** (DA 91) | Business Google account | User: log in, create listing |
| **AlternativeTo** (DA 70+) | 7-day age gate | Submit June 1+ (gate lifts now) |
| **Indie Hackers** (DA 65+) | Logo upload blocked | User: upload favicon-256.png |
| **Find Your Newsletter** (DA ~30) | reCAPTCHA | User: complete CAPTCHA |
| **PostApex** (DA ~35) | Account signup | User: create publisher account |
| **Reletter** (DA ~50) | Auto-indexing | Check back 2-4 weeks |
| **Tier 5 listicles** (8 targets) | Outreach not started | Begin after June submissions settle |

### Reddit Expansion
| Account | Product | Status | Target |
|---------|---------|--------|--------|
| Khavel_dev | DevAI Semanal | Phase 1 warm-up active | Phase 2: June 25+ |
| (TBD — xGNerd) | FutPicks | Not started | After DevAI warm-up proves safe |
| (TBD) | NbaPropLab | Not started | After DevAI warm-up proves safe |

### Other Open Items
- [ ] **FutPicks `docs-site` deploy** — publish corrected `llms.txt` (rides its own pipeline, separate from the API deploy)
- [ ] Newsletter swaps (June+): identify 5-10 ES tech + 5-10 EN AI newsletters; craft swap pitch
- [x] **NbaPropLab SSR deploy fix** ✅ RESOLVED (2026-06-02) — SSR Node server is now deployed (Dockerfile runs `server.mjs`, nginx proxies `@ssr`); player/landing pages render server-side (`/nba-player-props` 799 words, `/players/*` 417). The remaining homepage-root bug (nginx served `index.csr.html` for `/`, so `/` was a 13-word shell) was fixed this session: added `location = /` serving the prerendered `index.html`, flipped `path:''` to `RenderMode.Prerender`, fixed canonical-domain split. **Homepage now 531 words to crawlers, canonical=nbaproplab.com, FAQ JSON-LD live.** Remaining backlog (separate): age-gate dedup, per-player prose, runtime title override ("Motor").
- [ ] **FutPicks SEO render fix** (task queued in Furbov2) — futpicks.com still serves a blank ~22KB CSR shell to non-JS crawlers for data routes (Angular `outputMode: "static"`, routes not prerendered). **Update (2026-06-02): the separate AI-crawler block is now LIFTED** (Cloudflare "Managed robots.txt" turned off → GPTBot/ClaudeBot/Google-Extended/PerplexityBot can crawl; was `Disallow: /` + 403). The render fix (prerender landing pages + SSR data routes with per-route meta) is still pending. (1 impression / 0 keywords today.)
- [ ] SEO fixes: FutPicks canonical URL bug (revisit after render fix)
- [ ] Community channels: Telegram (DevAI), Discord (NbaPropLab), LinkedIn (DevAI)

---

## Recurring Tasks (automated via Claude Code)

### 1. Twitter Daily Posts — 3:00 PM CET (Sonnet)
- **@DevAISemanal** (1-2/day, Spanish AI dev tips)
- **@StatLineNerd** (NBA **and WNBA** picks via `proplab` MCP, year-round; attaches pick cards via `--pick-id`)
- **@FutProbLab** (football picks via `footballlab` MCP, bilingual; cards pending endpoint un-gate)
- Anti-detection: 7-10 min gap between accounts, 2-4h same-account, no cross-referencing
- Data fallback: if an MCP is down → educational/methodology content (never skip the account)
- **Docs:** `C:\Users\ceja_\.claude\scheduled-tasks\twitter-daily-posts\SKILL.md`

### 2. Twitter Engagement — 5:00 PM CET (Sonnet)
- Likes/replies/quote-tweets via Chrome (headless API can't engage). Trains each For-You algo.
- **Docs:** `...\twitter-engagement\SKILL.md`

### 3. Reddit Warm-Up Comments — daily (Phase 1: May 26 – June 25)
- Khavel_dev, 2-5 genuine helpful comments/day, zero promotion. **Docs:** `...\reddit-warmup-comments\SKILL.md`

### 4. Cross-Post Articles — 11:00 AM CET
- Ghost latest article → Dev.to / Medium / Hashnode / **Substack** (4 platforms), 24h after publish, canonical → devaisemanal.com. Author: Khavel. **Docs:** `...\crosspost-articles\SKILL.md`

### 5. Reddit Phase 2 Transition — one-time June 25, 2026
- Assess Khavel_dev readiness (30d age + 100 karma), GO/NO-GO + first 4 post templates. **Docs:** `...\reddit-phase2-transition\SKILL.md`

---

## Timeline

```
May 2026    ████████████████████████████████
        25-27  ✅ Directory submissions, Reddit warm-up, Twitter API setup
        27     ✅ Medium + Hashnode + Substack cross-posts (4-platform)
        29     ✅ NBA proplab MCP integration (replaces dead nba-edge); WNBA year-round
        29     ✅ Live tweets verified (StatLineNerd + FutProbLab); pick-card render fixed
        30     ✅ Football footballlab MCP registered + integrated; card redesigned
        30     ✅ Image tweets live (Chrome + API); media.write re-auth; media upload built

June 2026   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
         1  ⏳ AlternativeTo + pending directories (G2, Indie Hackers, PostApex)
        15  ⏳ Tier 5 listicle outreach
        25  ⏳ Reddit Phase 2 — first promotional post (Khavel_dev)
            ⏳ Un-gate FutPicks card endpoint → @FutProbLab image tweets
            ⏳ docs-site deploy (llms.txt)

July 2026   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
            ⏳ Newsletter swaps · FutPicks/NbaPropLab Reddit warm-up · Telegram/Discord
            ⏳ GitHub PR follow-ups · SEO fixes (NbaPropLab SSR, FutPicks canonical)

Aug 2026    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
            ⏳ Verify backlinks indexed · LinkedIn presence · 2nd-wave listicles
```

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `seo/CLAUDE.md` | Twitter API, media attach, cross-posting, Reddit (auto-loaded) |
| `seo/twitter_api_post.py` | Tweet posting (all 3 accounts) + image upload (`--pick-id`/`--image-url`/`--image`) |
| `seo/oauth2_exchange.py` | OAuth 2.0 PKCE token exchange (scopes incl. `media.write`) |
| `seo/twitter_post_log.jsonl` | Tweet log (append-only) |
| `seo/API_SCHEMAS_NBA.md` | Real `proplab` MCP response schemas (ground truth) |
| `seo/API_SCHEMAS_FUTPICKS.md` | Real `footballlab` MCP response schemas (ground truth) |
| `seo/API_INTEGRATION_PLAN_NBA.md` | NBA/WNBA MCP → Twitter spec (MCP-first) |
| `seo/API_INTEGRATION_PLAN_FUTPICKS.md` | Football MCP → Twitter spec (MCP-first) |
| `seo/crosspost_log.jsonl` | Cross-post tracking (4 platforms) |
| `seo/directory-submissions.md` | Directory submission tracker |
| `seo/reddit_post_comment.py` · `reddit_lessons_learned.md` | Reddit automation + lessons |
| `seo/LEARNINGS.md` | SEO strategy learnings |

**MCP servers (in `~/.claude.json`):** `proplab` (NBA/WNBA, nbaproplab.com) · `footballlab` (football, futpicks.com). Both load at Claude Code startup.

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| All 3 Twitter accounts share phone 696295730 | One suspension → all flagged | If any gets a warning, pause ALL 48h |
| **Graduated access** ("Unlock more on X") now on all 3 accounts | Replies may be filtered; reach limited | API posts/likes still work; engage organically to graduate; monitor |
| Reddit Khavel_dev caught as bot | Ban, lost warm-up | Strict anti-AI style, varied formatting, human timing |
| X API credits depleted | Can't post via API | Chrome MCP fallback (free); monitor balance |
| OAuth 2.0 token refresh fails | Posting breaks (DevAISemanal/StatLineNerd) | Re-authorize via `oauth2_exchange.py` (keep `media.write` in scope) |
| MCP server down (proplab/footballlab) | No live data for tweets | SKILL falls back to educational content; both have public endpoints |
| GitHub PRs not merged | Lose DA 96 backlinks | Follow up after 4 weeks |
| Cross-post platform login expires | Chrome automation fails silently | Task logs failure, retries next day |
