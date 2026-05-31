# DevAI Semanal — Project Instructions

## Project Overview

Multi-product promotion and content infrastructure for 3 products:

| Product | Domain | Twitter | Focus |
|---------|--------|---------|-------|
| **DevAI Semanal** | devaisemanal.com | @DevAISemanal | AI dev tips newsletter (Spanish) |
| **NbaPropLab** | nbaproplab.com | @StatLineNerd | NBA **& WNBA** player props scoring engine |
| **FutPicks** | futpicks.com | @FutProbLab | European football betting model (FootballLab API) |

## Repository Structure

```
run.py                  # Newsletter pipeline entry point
config.yaml             # RSS feeds, Claude model config
src/                    # Pipeline phases: sourcing → curation → rewriting → assembly → publishing
templates/              # Jinja2 HTML/TXT newsletter templates
seo/                    # Promotion infrastructure (Twitter, Reddit, SEO, directories)
  twitter_api_post.py   # Official X API posting script (all 3 accounts)
  oauth2_exchange.py    # OAuth 2.0 PKCE helper for multi-account auth
  reddit_post_comment.py # Reddit comment automation
  crosspost_log.jsonl   # Cross-post tracking log (Medium/Hashnode/Dev.to)
  .env.twitter          # Twitter API credentials (GITIGNORED)
  ga_admin.py           # GA4 Admin API CLI (list/ensure/retention)
```

## Twitter/X API — Quick Reference

See `seo/CLAUDE.md` for full details. Quick usage:

```bash
cd seo/
python twitter_api_post.py --account FutProbLab "tweet text"
python twitter_api_post.py --account DevAISemanal "tweet text"
python twitter_api_post.py --account StatLineNerd "tweet text"
python twitter_api_post.py --account FutProbLab --dry-run "preview without posting"
python twitter_api_post.py --account FutProbLab "reply text" --reply-to https://x.com/user/status/123
python twitter_api_post.py --account StatLineNerd "Top pick" --pick-id 380921   # attach NBA pick card
```

## Live Data — MCP Servers

Tweet content is driven by live model data via two MCP servers (registered in `~/.claude.json`, load at startup):

| MCP | Product | Tools | Auth |
|-----|---------|-------|------|
| `proplab` | NbaPropLab (NBA **& WNBA**) | `proplab_dashboard`, `proplab_track_record`, `proplab_pick_details`, `proplab_games` | public (no auth) |
| `footballlab` | FutPicks (futpicks.com) | `flab_picks_today`, `flab_picks_board`, `flab_matches_today`, `flab_track_record`, … | public (no auth) |

- The old `nba-edge` MCP is **dead** — do not use it.
- Real response schemas: `seo/API_SCHEMAS_NBA.md`, `seo/API_SCHEMAS_FUTPICKS.md`. Integration specs: `seo/API_INTEGRATION_PLAN_{NBA,FUTPICKS}.md`.
- @StatLineNerd attaches pick cards via `--pick-id` (needs `media.write` scope — already granted 2026-05-30).

## Google Analytics (GA4)

All 3 sites have GA4 tags live (installed 2026-05-31). Properties live under GA account **"Khavel Projects" (396315220)**. Data retention set to 14 months (max) on all.

| Product | Domain | Measurement ID | Property | Tag location |
|---------|--------|----------------|----------|--------------|
| DevAI Semanal | devaisemanal.com | `G-FJDCNK1Y8K` | 539660132 | Ghost → Code injection → Site Header |
| NbaPropLab | nbaproplab.com | `G-TPF6L8XLLV` | 539606177 | `nbav3-client/src/index.html` (SSR) |
| FutPicks | futpicks.com | `G-RFXN4QE9FL` | 539652295 | `footballlab-web/src/index.html` (SSR) |

- **CLI tool:** `python seo/ga_admin.py {list|ensure|retention}` — manage GA4 via Admin API.
  - `list` → every property + Measurement ID. `ensure --account 396315220 --name … --domain …` → idempotent find-or-create. `retention` → bump all props to 14-month data retention.
- **Auth:** user OAuth as khavel112@gmail.com, token at `seo/.ga-oauth-token.json` (gitignored, auto-refreshes). Service-account route does NOT work (GA rejects SA emails). To re-consent: tiny `InstalledAppFlow` script using `gsc-oauth-client.json` with scopes `analytics.edit`+`analytics.readonly`.
- **Admin client is `v1alpha`** — import types from `google.analytics.admin_v1alpha` (NOT v1beta — mismatch raises TypeError on create).
- **GCP project:** `testvpn-262120` (861555918471). Analytics Admin API enabled there. Ghost settings PUT returns **501** (Ghost-on-Fly limitation) — DevAI tag must be pasted via Ghost UI, not the API.
- **Pi-hole note:** `analytics{admin,data}.googleapis.com` + `serviceusage`/`oauth2`/`accounts.google.com` are allowlisted on Firebat (192.168.1.21); they were blackholed by the Hagezi blocklist. Re-run `docker exec pihole pihole allow <host>` if DNS breaks.
- **Reading traffic in chat:** the official **`google-analytics` MCP** (`analytics-mcp`, registered in `~/.claude.json`) is read-only — tools: `get_account_summaries`, `get_property_details`, `run_report`, `run_realtime_report`, `run_funnel_report`, `run_conversions_report`, `get_custom_dimensions_and_metrics`, `list_property_annotations`, `list_google_ads_links`. Auth via ADC at `seo/.ga-adc.json` (built from the OAuth token; gitignored), project `testvpn-262120`. Loads at Claude Code startup. Ask e.g. "how many users did futpicks get this week?".
- **Pending:** GA4 ↔ Search Console links (Admin API does NOT support this — UI-only, do via Chrome). Full runbook + the stale-ref automation lesson: `seo/GA4_SEARCH_CONSOLE_LINK.md`.

## Cross-Posting — Quick Reference

Articles published on devaisemanal.com (Ghost) are automatically cross-posted to 4 platforms via the `crosspost-articles` scheduled task. See `seo/CLAUDE.md` for full details.

| Platform | URL | Auth | Canonical |
|----------|-----|------|-----------|
| **Dev.to** | dev.to/khavel | GitHub OAuth (browser session) | `canonical_url` in frontmatter |
| **Medium** | medium.com/@khavel | Browser session | Auto-set via "Import a story" |
| **Hashnode** | devaisemanal.hashnode.dev | Browser session | "Are you republishing?" checkbox |
| **Substack** | khavel.substack.com | Browser session | No canonical override; in-body attribution link |

- **Author on all platforms: "Khavel"** — never use real name
- **Canonical URLs always → devaisemanal.com** (SEO: all link equity flows to original)
- **24h cooling period** — task waits ≥24h after Ghost publish before cross-posting
- **Log:** `seo/crosspost_log.jsonl`

## Environment & Secrets

- `.env` — ANTHROPIC_API_KEY, BEEHIIV_*, TELEGRAM_* (newsletter pipeline)
- `seo/.env.twitter` — All Twitter/X API credentials (OAuth 1.0a + OAuth 2.0)
- `seo/.twitter-oauth2-tokens/` — OAuth 2.0 PKCE tokens per account (auto-refresh)
- `seo/.ga-oauth-token.json`, `seo/.ga-adc.json` — GA4 user OAuth token + ADC (gitignored)
- All secrets are gitignored. Never commit them.

## Scheduled Tasks (Claude Code)

| Task | Schedule (CET) | Model | Purpose |
|------|---------------|-------|---------|
| `twitter-daily-posts` | Daily 3:00 PM | Sonnet | Tweet live model data (proplab/footballlab MCP) via X API, + pick-card images |
| `twitter-engagement` | Daily 5:00 PM | Sonnet | Likes/replies via Chrome |
| `reddit-warmup-comments` | Daily 10:26 AM | Opus | Reddit value comments (Phase 1) |
| `crosspost-articles` | Daily 11:00 AM | Default | Cross-post new articles to Medium/Hashnode/Dev.to/Substack |
| `reddit-phase2-transition` | June 25 one-time | Default | Assess Reddit promo readiness |

Task files live in `C:\Users\ceja_\.claude\scheduled-tasks\<task-id>\SKILL.md`.

## Key Constraints

- **Windows environment** — Spanish locale (es-ES). Use PowerShell for shell commands.
- **Python 3.12** — venv at project root
- **Claude model** — `claude-sonnet-4-20250514` for pipeline, configured in config.yaml
- **Anti-detection** — Never cross-reference the 3 Twitter accounts. No RT/like between them.
- **Phone number** — All 3 Twitter accounts share phone 696295730. Risk of linked suspension.
