# SEO & Promotion — Detailed Instructions

## Twitter/X API Setup

### Accounts & Auth Methods

| Account | Handle | Product | Auth | Token Location |
|---------|--------|---------|------|---------------|
| FutProbLab | @FutProbLab | FutPicks | OAuth 1.0a | `.env.twitter` (direct access tokens) |
| DevAISemanal | @DevAISemanal | DevAI Semanal | OAuth 2.0 PKCE | `.twitter-oauth2-tokens/devaisemanal_token.json` |
| StatLineNerd | @StatLineNerd | NbaPropLab | OAuth 2.0 PKCE | `.twitter-oauth2-tokens/statlinenerd_token.json` |

### App: PropLab Tools (ID: 32989211)
- **Plan:** Pay Per Use (~$0.015/text tweet, ~$0.20/tweet with URL)
- **Console:** https://console.x.com/accounts/2059623409512812544/apps/32989211
- **Billing:** https://console.x.com → Billing → Credits ($25 loaded 2026-05-27)

### Credentials File: `.env.twitter`

Contains all API credentials. Structure:
```
TWITTER_CLIENT_ID=...          # OAuth 2.0 Client ID
TWITTER_CLIENT_SECRET=...      # OAuth 2.0 Client Secret
TWITTER_API_KEY=...            # OAuth 1.0a Consumer Key
TWITTER_API_SECRET=...         # OAuth 1.0a Consumer Key Secret
TWITTER_BEARER_TOKEN=...       # App-only Bearer Token (URL-encoded, %2F etc. are intentional)
FUTPROBLAB_ACCESS_TOKEN=...    # OAuth 1.0a Access Token for @FutProbLab
FUTPROBLAB_ACCESS_TOKEN_SECRET=...
DEVAISEMANAL_ACCESS_TOKEN=     # Empty — uses OAuth 2.0 PKCE instead
STATLINENERD_ACCESS_TOKEN=     # Empty — uses OAuth 2.0 PKCE instead
```

### Posting Tweets

**Primary method — API script:**
```bash
cd "C:\Users\ceja_\Desktop\Desarrollos\Spam\devai-newsletter\seo"

# Post a tweet
python twitter_api_post.py --account FutProbLab "Your tweet text here"
python twitter_api_post.py --account DevAISemanal "Tu tweet aqui"
python twitter_api_post.py --account StatLineNerd "NBA analysis tweet"

# Post from file
python twitter_api_post.py --account FutProbLab --file tweet_draft.txt

# Reply to a tweet
python twitter_api_post.py --account FutProbLab "Reply text" --reply-to https://x.com/user/status/123

# Attach an image (NEW):
python twitter_api_post.py --account StatLineNerd "Top pick" --pick-id 380921      # NBA pick card PNG
python twitter_api_post.py --account StatLineNerd "Top pick" --image-url https://nbaproplab.com/api/v1/screenshots/pick/380921.png
python twitter_api_post.py --account StatLineNerd "Top pick" --image C:\path\card.png

# Dry run (preview without posting)
python twitter_api_post.py --account FutProbLab --dry-run "Test"
```

### Image / media attachment
- **`--pick-id <id>`** — attaches the NbaPropLab pick card (`/api/v1/screenshots/pick/{id}.png`). **`--image-url`** / **`--image`** for any other image.
- **OAuth2 accounts (@StatLineNerd, @DevAISemanal):** upload uses the X API v2 `media/upload` endpoint and needs the **`media.write`** scope. @StatLineNerd was re-authorized with it on 2026-05-30; @DevAISemanal would need a re-auth (`oauth2_exchange.py`) before it can attach media.
- **OAuth1 account (@FutProbLab):** uses v1.1 `media_upload` (no scope re-auth needed) — but the football card endpoint is still 401-gated, so no card to attach yet.
- Works headlessly (no Chrome) — this is the path the scheduled task uses for image tweets.

**How it works internally:**
- @FutProbLab: Uses `tweepy` with OAuth 1.0a (Consumer Key + Access Token from `.env.twitter`)
- @DevAISemanal/@StatLineNerd: Uses `httpx` with OAuth 2.0 Bearer token from `.twitter-oauth2-tokens/`
- OAuth 2.0 tokens auto-refresh using the saved `refresh_token`
- All posts are logged to `twitter_post_log.jsonl`

**Fallback — Chrome MCP (free, no API credits needed):**
All 3 accounts are logged into Chrome with account switching.
1. Navigate to `https://x.com/home`
2. Switch account: `document.querySelector('button[data-testid="SideNav_AccountSwitcher_Button"]').click()`
3. Compose and post via UI automation
4. Manually log the tweet to `twitter_post_log.jsonl`

### Scheduled Tasks

| Task | Schedule (CET) | Model | What |
|------|---------------|-------|------|
| `twitter-daily-posts` | Daily 3:00 PM | Sonnet | Draft + post tweets via API |
| `twitter-engagement` | Daily 5:00 PM | Sonnet | Likes/replies via Chrome browser |

Task files: `C:\Users\ceja_\.claude\scheduled-tasks\twitter-daily-posts\SKILL.md` and `twitter-engagement\SKILL.md`

### Tweet Log Format

File: `twitter_post_log.jsonl` — append-only JSONL:
```json
{"timestamp": "2026-05-27T16:11:41+00:00", "date": "2026-05-27", "time": "16:11:41", "account": "FutProbLab", "handle": "@FutProbLab", "product": "FutPicks", "action": "tweet", "tweet_id": "2059638142693417252", "text_preview": "First 100 chars...", "method": "api"}
```
The `timestamp` field (ISO 8601 with timezone) is the canonical time reference. Legacy `date`/`time` fields kept for backward compatibility. Always check this log before posting to avoid duplicate content.

### OAuth 2.0 Token Refresh

Tokens expire in ~2 hours but auto-refresh via `refresh_token`. If a token expires and refresh fails:
```bash
# Re-authorize using the helper script
python oauth2_exchange.py generate
# Copy the AUTH_URL, open in browser at x.com (not twitter.com!), authorize
# The page redirects to localhost:3000/callback (will fail to load — that's expected)
# Copy the full redirect URL from the browser address bar
python oauth2_exchange.py exchange "https://localhost:3000/callback?state=...&code=..." DevAISemanal
```

**Critical:** Use `x.com` domain for the OAuth URL (not `twitter.com`) — x.com shares the browser session with the logged-in accounts. The OAuth consent page has an account-picker dropdown if you need to switch which account to authorize.

### Regenerating Credentials

If Consumer Key is regenerated on the developer console:
1. **All Access Tokens become invalid** — they're cryptographically bound to the Consumer Key
2. Must regenerate Access Token for @FutProbLab on the console
3. Must re-authorize @DevAISemanal and @StatLineNerd via OAuth 2.0 PKCE
4. **Use JavaScript DOM extraction** to read credentials from console modals — NEVER trust screenshot OCR for credentials

### Content Strategy (per account)

**@DevAISemanal** (1-2 tweets/day, Spanish):
- AI tool tips (40%), newsletter teasers (20%), build-in-public (20%), hot takes (20%)
- Developer tone, practical, code snippets

**@StatLineNerd** (3-5 tweets on slate days, English, **NBA + WNBA — effectively year-round**):
- Daily picks with scores (40%), pre-game analysis (25%), results transparency (20%), educational (15%)
- Data nerd tone, always include score/100 and direction; attach the pick card via `--pick-id`
- **Data source:** `proplab` MCP (`proplab_dashboard`, `proplab_track_record`, …) — see `API_SCHEMAS_NBA.md`

**@FutProbLab** (3-5 tweets on match days, bilingual en/es):
- Match picks with edge% (40%), weekend previews (25%), results (20%), educational (15%)
- Analytical tone, Poisson model; **filter on edge, not score**; lead transparency with ROI
- **Data source:** `footballlab` MCP (`flab_picks_today`, `flab_track_record`, …) — see `API_SCHEMAS_FUTPICKS.md`

### Anti-Detection Rules

- **Never cross-reference accounts** — no RT/like/reply between @DevAISemanal, @StatLineNerd, @FutProbLab
- **Vary posting times** — don't post at the same minute every day
- **Space between accounts** — 5-10 min gap between posting from different accounts
- **Space between tweets** — minimum 30 min on same account, ideally 2-4 hours
- **Mix content types** — not all broadcast. Include replies, likes, organic engagement
- **All 3 accounts share phone 696295730** — if one gets flagged, pause all for 48h

---

## Cross-Posting (DevAI Semanal Articles)

### Strategy
Every article published on devaisemanal.com (Ghost CMS) gets cross-posted to 3 platforms for SEO backlinks and discovery. All copies have `<link rel="canonical">` pointing back to devaisemanal.com so Google attributes link equity to the original.

### Accounts & Platforms

| Platform | Profile URL | Auth Method | How Canonical is Set |
|----------|------------|-------------|---------------------|
| **Dev.to** | dev.to/khavel | GitHub OAuth (browser session) | `canonical_url` field in article frontmatter |
| **Medium** | medium.com/@khavel | Google OAuth (browser session) | Auto-set via "Import a story" feature |
| **Hashnode** | devaisemanal.hashnode.dev | Email/password (browser session) | "Are you republishing?" → "Add a canonical URL" checkbox |
| **Substack** | khavel.substack.com | Browser session | No canonical override — backlink via in-body attribution link |

### Identity Rules
- **Author name: "Khavel"** on ALL platforms — never use real name
- **Bio/tagline:** "Building DevAI Semanal — AI dev tips newsletter"
- Hashnode profile was changed to "Khavel" on 2026-05-27

### Scheduled Task: `crosspost-articles`
- **Schedule:** Daily at 11:00 AM CET
- **How it works:**
  1. Queries Ghost Admin API for latest published post (`python _list_ghost_posts.py`)
  2. Checks `seo/crosspost_log.jsonl` — skips if already cross-posted
  3. Checks timing — only acts if article was published ≥24h ago (Google indexing window)
  4. Cross-posts via Chrome browser automation to all 4 platforms
  5. Verifies `<link rel="canonical">` on each published page
  6. Logs results to `crosspost_log.jsonl`
- **Task file:** `C:\Users\ceja_\.claude\scheduled-tasks\crosspost-articles\SKILL.md`

### Platform-Specific Procedures

**Dev.to:**
1. Navigate to `https://dev.to/new`
2. Use markdown editor with frontmatter: `canonical_url: https://devaisemanal.com/{slug}/`
3. Tags: ai, automation, python, newsletter
4. Publish directly

**Medium:**
1. Use "Import a story" (avatar → Stories → Import)
2. Paste the original URL — Medium auto-imports content AND sets canonical
3. Add tags: AI, Automation, Python, Newsletter, Software Development
4. Review formatting, then Publish

**Hashnode:**
1. Create new draft at hashnode.com/drafts
2. Switch to Markdown mode (••• → Markdown)
3. Use `form_input` on textarea ref (not `type` — avoids title field collision)
4. Draft settings → Discovery → "Are you republishing?" → check → add canonical URL
5. Tags: #ai, #automation, #python
6. Publish

**Substack:**
1. Navigate to `https://khavel.substack.com/publish/post` (creates new draft)
2. Set title and subtitle
3. Inject body content via ClipboardEvent with `text/html` MIME type (Substack uses ProseMirror)
4. Add "Publicado originalmente en devaisemanal.com" with link at bottom of article (this is the backlink — Substack has no canonical URL field)
5. Post Settings → Tags: ai, automation, python
6. SEO Options: title and description auto-filled from post
7. Publish → "Publish without buttons" (skip subscribe buttons prompt)

### Substack Quirks
- **No canonical URL field** — SEO Options only has: SEO title, SEO description, Post URL (slug). Backlink comes from in-body attribution link only.
- **ProseMirror editor** — use ClipboardEvent with `text/html` for rich content injection. `type` tool works for plain text only.
- **Self-canonicalizes** — `<link rel="canonical">` always points to `khavel.substack.com`, cannot override.
- **Subscribe buttons prompt** — on publish, Substack asks to add subscribe buttons. Choose "Publish without buttons" for cross-posted content.
- **DA 93 backlink value** — even without canonical, the in-body link to devaisemanal.com from a DA 93 domain is high-value.

### Hashnode Quirks (learned the hard way)
- **SPA freezes frequently** — CDP screenshot timeouts. Fix: close tab, create new one, retry
- **Don't use `type` for body text** — it merges into the title field. Use `form_input` with the textarea's ref instead
- **Cloudflare challenge on public pages** — wait 5-10 seconds for auto-solve
- **Profile changes need explicit Save** — click "Save changes" button immediately after editing
- **GraphQL API requires Pro plan** (paid, since May 2026) — Chrome automation is the only free option

### Cross-Post Log Format

File: `seo/crosspost_log.jsonl` — append-only JSONL:
```json
{"timestamp": "2026-05-27T19:45:00+02:00", "ghost_slug": "como-automatice-newsletter-ia-developers", "ghost_url": "https://devaisemanal.com/como-automatice-newsletter-ia-developers/", "platform": "hashnode", "crosspost_url": "https://devaisemanal.hashnode.dev/...", "canonical_url": "https://devaisemanal.com/como-automatice-newsletter-ia-developers/", "status": "published", "error": null}
```

### Verifying Canonical URLs
After publishing on any platform, verify with JavaScript in the browser:
```javascript
document.querySelector('link[rel="canonical"]')?.href
// Should return: https://devaisemanal.com/{slug}/
```

### Current Cross-Posts

| Article | Dev.to | Medium | Hashnode | Substack |
|---------|--------|--------|---------|----------|
| Cómo automaticé una newsletter de IA... | ✅ dev.to/khavel/...3fje | ✅ medium.com/p/cd36cef24c03 | ✅ devaisemanal.hashnode.dev/c-mo-... | ✅ khavel.substack.com/p/como-automatice-... |

---

## Reddit Automation

### Account: Khavel_dev
- Used for AI-agent themed promotion across r/microsaas, r/ClaudeAI, r/SideProject, r/SaaS
- Warmup phase: value comments before any self-promotion (6-week schedule)

### Scripts
- `reddit_post_comment.py` — Post comments via old.reddit.com API
- `reddit_session.py` — Manage browser session/cookies
- `reddit_agent.py` — Automation agent
- Log: `reddit_comment_log.jsonl`

---

## Directory Submissions

Track all submissions in `directory-submissions.md`. Key directories:
- Paved (DA ~55, dofollow) — submitted
- Crunchbase (DA 91) — submitted
- G2 (DA 91) — pending (needs business Google account)
- AlternativeTo (DA 70+) — pending
- Indie Hackers (DA 65+) — submitted
- Product Hunt — launched

---

## Troubleshooting

### Twitter API 401 Unauthorized
1. Check if Consumer Key was regenerated (invalidates all Access Tokens)
2. Check if OAuth 2.0 token expired (refresh or re-authorize)
3. Verify credentials with: `python -c "import tweepy; ..."`  using Bearer token first

### Windows Encoding Issues
The script has `sys.stdout.reconfigure(encoding='utf-8')` at the top. If emoji still crash:
- Use PowerShell (not cmd.exe)
- Or set `$env:PYTHONIOENCODING = 'utf-8'` before running

### OAuth 2.0 PKCE Flow Fails
- tweepy's `get_me()` doesn't work with OAuth 2.0 user tokens — use httpx directly
- The PKCE `code_verifier` must persist between URL generation and token exchange — use `oauth2_exchange.py` (not the built-in `--auth` flow which uses interactive `input()`)
