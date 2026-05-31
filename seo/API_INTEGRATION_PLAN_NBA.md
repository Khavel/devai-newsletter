# NbaPropLab — Integration Plan for Twitter Automation (@StatLineNerd)

> **Account:** @StatLineNerd
> **Status (2026-05-29):** ✅ Integration path resolved. The `proplab` MCP server is **live** and replaces the dead `nba-edge` MCP. Schema discovery is **done** — see `API_SCHEMAS_NBA.md`.
> **Primary path:** `proplab` MCP tools (no API key needed for daily content).
> **Fallback:** raw HTTP API at `nbaproplab.com/api/v1/...` with `X-API-Key` (only needed for on-demand scoring / detailed backtests).

---

## TL;DR — what changed

1. The old `nba-edge` MCP (GetTodayEdges, GetYesterdayResults) is **disconnected/dead**. Stop referencing it.
2. The new `proplab` MCP is the integration. `proplab_dashboard` + `proplab_track_record` are **public, no auth** and cover all daily tweet content.
3. The model scores **NBA *and* WNBA**. As of late May the NBA is at the Finals (1 game/night) and **WNBA is the main slate** — almost all Good picks are WNBA. Handle both leagues.
4. The MCP `summary`/`explanation` fields are **Spanish**. @StatLineNerd posts in **English**, so build English copy from the structured fields (don't paste `summary` verbatim).
5. No API-key creation is required to ship the daily routine. The blocker is gone.

---

## Integration path: proplab MCP

| Need | Tool | Auth | Key fields |
|------|------|------|-----------|
| Pre-flight health check | `proplab_system_status` | public | `health.status`, `freshness[].status` |
| Today's games | `proplab_games` / `proplab_dashboard` | public | `games[]`, `gamesCount` |
| Today's scored picks | `proplab_dashboard` | public | `topPicks[]`, `ratingDistribution` |
| Yesterday's results | `proplab_track_record` | public | `dailyResults[0]`, `recentGoodPicks[]` (with `hit`/`actualValue`) |
| Season record / ROI | `proplab_track_record` | public | `overallHitRate`, `goodPicks.{hitRate,roi}`, `totalProfit` |
| Spider chart + deep analysis | `proplab_pick_details` | public | `finalSpider.axes`, `blocks[].explanation` |
| On-demand scoring | `proplab_evaluate_pick` | **auth** | score + block breakdown |
| Detailed backtests | `proplab_backtest_*` | **auth** | hit rate / ROI by tier/stat/day |

**League filter:** pass `league: "nba"` or `league: "wnba"` to `dashboard`/`track_record` to split, or omit to get both.

> Full response schemas with every field: **`API_SCHEMAS_NBA.md`**.

---

## Daily routine flow (API-direct via MCP)

```
0. proplab_system_status → if health critical AND freshness all stale → educational fallback, skip picks
1. proplab_dashboard (today) → read games[] and topPicks[]
   - gamesCount == 0 → no slate → educational/methodology tweet → done
2. Filter topPicks: rating == "Good" (scoreFinal >= 63), isVoided == false, isPeriodDataGap == false
   - none Good → fall back to top "Marginal" (>=60) with a softer framing, or educational
3. Pick top 2-3 by scoreFinal. For each, optionally proplab_pick_details(id) to pull
   the dominant block explanation for a reasoning line.
4. Build ENGLISH tweet copy from structured fields (see template). Do NOT paste the Spanish summary.
5. Post via twitter_api_post.py --account StatLineNerd, 2-4h spacing between tweets.
6. proplab_track_record → build yesterday's results recap from dailyResults[0] + settled recentGoodPicks.
7. Post results recap (morning slot, before new picks).
```

### League handling
- Tag each pick's league. Hashtags: `#NBA #NBAProps` vs `#WNBA #WNBAProps`.
- During the NBA Finals + WNBA regular season overlap (now), expect the slate to be WNBA-heavy. That's fine — @StatLineNerd covers both; the brand is "the props model," not NBA-only.
- If you want to keep accounts league-pure later, add a `league` config flag. For now, post whatever has Good picks.

### Error / empty handling
- MCP tool error or `health.status == "down"` → educational content (never skip the account silently).
- Empty Good picks → post a "Marginal slate today" note or educational pillar content.
- Stale freshness (data older than tip-off) → caveat the tweet or defer to educational.

---

## Tweet templates (English copy from structured fields)

### Single pick
Built from `playerName`, `stat`, `direction`, `line`, `scoreFinal`, `rating`, top `blockScores`, `teamAbbreviation`/`opponentAbbreviation`, `league`.

```
🔥 Top Pick — Paige Bueckers (DAL vs LVA)
Rebounds+Assists OVER 8.5

Model score: 65/100 (Good)
Edge drivers: Analysis Quality 84 · Market Line 66

#WNBA #WNBAProps #Aces
```

> Map stat codes to readable labels: `PtsRebAst`→"Pts+Reb+Ast", `RebAst`→"Reb+Ast", `PtsAst`→"Pts+Ast", `PtsReb`→"Pts+Reb", `Threes`→"3PT Made". `ratingEmoji` (🔥 Good / ✅ Marginal) can lead the tweet.

### Results / transparency recap
Built from `track_record.dailyResults[0]` + settled `recentGoodPicks` (those with `hit`/`actualValue`).

```
📊 Yesterday (May 27): 84-79 on the full slate

Good-rated picks tracked:
✅ Courtney Williams R+A O8.5 → 10
✅ Kahleah Copper PRA U24.5 → 23
❌ Angel Reese PRA O28.5 → 23

Season: 55.2% hit · Good picks 63.2% (+20.8% ROI)
#WNBA #NBAProps
```

> The **season credibility line** — "Good picks 63.2% hit, +20.8% ROI over 2,820 picks" — is the strongest recurring hook. Use it in recaps and educational tweets.

### Analysis thread (1-2/week)
Use `proplab_pick_details(id)` → `finalSpider.axes` for the 7-block radar and `blocks[].explanation` for per-block reasoning (translate the Spanish narrative to English). One tweet per dominant block.

---

## Pick card images (Phase 2)

**Good news — we don't need to render the radar ourselves.** The web app already produces a per-pick share card (its OG image), publicly fetchable:

```
GET https://nbaproplab.com/api/v1/screenshots/pick/{id}.png    → 1200×675 PNG, public, no auth
```
(It's the `og:image`/`twitter:image` for `/picks/{id}`. The HTML wrapper is `/api/v1/og/pick/{id}`.)

The card shows the score badge, player, matchup, bet line, cover probability, the 7-factor spider, and PropLab branding.

### ✅ Both blockers resolved (2026-05-30)
1. **Render bug — FIXED.** The spider chart now plots correctly (labeled axes, filled polygon, factor bars, reason line). The card communicates value to a cold viewer.
2. **Media upload — BUILT.** `twitter_api_post.py` now uploads + attaches images: OAuth2 accounts via the X v2 `media/upload` endpoint, OAuth1 via v1.1. **@StatLineNerd was re-authorized with the `media.write` scope** on 2026-05-30. Verified end-to-end (download → upload → media_id).

### How to post a card (live, headless)
```bash
python twitter_api_post.py --account StatLineNerd --file tweet.txt --pick-id <id>
```
`--pick-id` pulls `GET /api/v1/screenshots/pick/{id}.png` (from `proplab_dashboard.topPicks[].id`), uploads it, and attaches `media_ids`. No need to render from `finalSpider.axes` ourselves — the endpoint is the source of truth. Lead the copy with the hook/CTA; the card carries the data. Image tweets ~2-3x engagement.

> Football equivalent (`futpicks.com/api/v1/screenshots/pick/{id}.png`) exists but is **401-gated** (FallbackPolicy) — would need an anonymous route or a token before @FutProbLab can use cards.

---

## Optional: raw HTTP API (fallback only)

Only needed for the auth-gated capabilities (on-demand scoring, detailed backtests) — the MCP covers everything else.

**Auth:** `X-API-Key: $NBAV3_DATA_TOKEN` (Sharp-tier). Create once via `POST /api/v1/me/api-keys` (JWT Bearer first), `rawKey` shown once.

**Base paths:** Data `https://nbaproplab.com/api/v1/data/...`; General `https://nbaproplab.com/api/v1/...` (games, track-record).

| Endpoint | MCP equivalent |
|----------|----------------|
| `GET /api/v1/data/picks/today` | `proplab_dashboard` |
| `GET /api/v1/data/picks/settled?from=&to=` | `proplab_track_record` (recentGoodPicks) |
| `GET /api/v1/games?date=` | `proplab_games` |
| `GET /api/v1/track-record` | `proplab_track_record` |
| `GET /api/v1/data/picks/{id}` | `proplab_pick_details` |
| `GET /api/v1/data/track-record/{summary,daily,by-market}` | `proplab_backtest_*` |

`seo/.env.twitter` additions (only if using HTTP fallback):
```
NBAPROPLAB_API_BASE=https://nbaproplab.com
NBAV3_DATA_TOKEN=...   # optional; from POST /api/v1/me/api-keys
```

---

## Pick rating tiers (confirmed live)

| Rating | Min score | Display | Today's count | Historical (Jan–May) |
|--------|-----------|---------|---------------|----------------------|
| Elite | — | — | 0 | 0 picks |
| Good | ≥ 63 | PREMIUM 🔥 | 7 | 2,820 · 63.2% · +20.8% ROI |
| Marginal | ≥ 60 | STANDARD ✅ | 34 | 6,210 · 59.2% · +13.1% ROI |
| Weak | ≥ 54 | internal | 141 | 20,436 · 52.9% · +1.1% ROI |
| Avoid | < 54 | internal | 304 | — |

**Only tweet Good (and occasionally top Marginal).** Weak/Avoid are internal.

---

## 7 scoring blocks & weights

Player Profile 25% · Matchup 20% · Game Context 15% · Market Line 15% · Synergy 10% · Analysis Quality 10% · External Signals 5%.

(Block sub-axes for thread content are listed in `API_SCHEMAS_NBA.md`.)

---

## Testing checklist

- [x] `proplab` MCP reachable; `proplab_system_status` returns health
- [x] `proplab_dashboard` returns topPicks with real fields (done — schema captured)
- [x] `proplab_track_record` returns season + daily + recentGoodPicks (done)
- [x] `proplab_pick_details` returns finalSpider + block explanations (done)
- [ ] English tweet formatter maps stat codes + builds copy from structured fields (NOT the Spanish summary)
- [ ] League routing: NBA vs WNBA hashtags
- [ ] Good-only filter (scoreFinal ≥ 63, not voided, no period gap)
- [ ] `--dry-run` pick tweet + results recap reviewed
- [ ] Tweet lengths < 280 chars
- [ ] Fallback to educational when slate empty / data stale
- [ ] (Phase 2) spider chart image from finalSpider.axes
