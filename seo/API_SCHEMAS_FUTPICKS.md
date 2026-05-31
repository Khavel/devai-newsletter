# FutPicks / FootballLab — Real MCP Response Schemas (Ground Truth)

> **Source:** Captured live from the `footballlab` MCP server's HTTP endpoints (`futpicks.com/api/*`) on 2026-05-29.
> **MCP server:** `footballlab-mcp-server`, registered in `.claude.json` as `footballlab` → tools are `mcp__footballlab__flab_*`. **Requires a Claude Code restart to load** (MCP servers load at startup).
> **Integration path:** Use the `flab_*` MCP tools. The 9 public tools need **no auth** and cover all daily tweet content.

---

## ⚠️ Three things that differ from the NBA (proplab) model

1. **Score scale is different — do NOT reuse NBA's score≥63 threshold.** A football pick rated **"Good" had `score: 32.43`**; a "Weak" one had `score: 13`. Rating is driven by **edge**, not raw score. **Filter on `rating` + `edge`, not score.**
2. **Narrative is bilingual and ready-made.** `narrativeJson` parses to `{ summary_en, summary_es, source, generatedAt }`. @FutProbLab is bilingual → use `summary_es` for La Liga, `summary_en` for PL/CL. (NBA gave Spanish-only.)
3. **Blocks are football-specific:** Form, H2H, Strength, HomeAway, Goals, Market, Context (each `*Score` 0-100 + `*Confidence` 0-1). Plus `blockDetails[]` like `PoissonGoals`.

---

## Public MCP tools (no auth) — daily content

| Tool | Purpose | HTTP endpoint |
|------|---------|---------------|
| `flab_picks_today` | Today's picks (default Good) | `/api/picks/today?date=&rating=&market=` |
| `flab_picks_board` | Full board w/ edge/odds/rating filters | `/api/picks/board?date=&league=&market=&rating=&minEdge=&...` |
| `flab_pick_details` | Single pick + block breakdown | `/api/picks/{id}` |
| `flab_matches_today` | Today's matches + embedded picks | `/api/matches/today` |
| `flab_match_details` | Single match (+`includeIntelligence`) | `/api/matches/{id}` / `/intelligence` |
| `flab_matches_upcoming` | Next N days (1-30) — **weekend preview** | `/api/matches/upcoming?days=` |
| `flab_track_record` | Settled performance (hit/profit/ROI) | `/api/track-record/filtered?...` |
| `flab_teams` | Team list | `/api/teams` |
| `flab_health` | API health | `/api/health` |

**Pro tools (need `FUTPICKS_API_KEY`):** `flab_picks_history`, `flab_evaluate_matches`, `flab_evaluate_match`, `flab_backtest_run`, `flab_export_picks`, `flab_data_catalog`.
**Ops tools (need `FUTPICKS_OPS_TOKEN`, admin):** `flab_ops_run`, `flab_ops_status`.

> The server is registered with **no tokens**, so only the public tools work until `FUTPICKS_API_KEY`/`FUTPICKS_OPS_TOKEN` are added to the `footballlab` env in `.claude.json`. Public tools fully cover Twitter content.

---

## Pick object (`flab_picks_today`, `flab_picks_board`, `flab_pick_details`)

Real "Good" pick (West Ham vs Wolves, 2026-04-10):

```jsonc
{
  "id": 247,
  "matchId": 12,
  "homeTeam": "West Ham", "awayTeam": "Wolves",
  "homeTeamLogo": "https://media.api-sports.io/football/teams/48.png",
  "awayTeamLogo": "https://media.api-sports.io/football/teams/39.png",
  "league": "Premier League",
  "kickoffUtc": "2026-04-10T19:00:00Z",
  "market": "H2H",                  // H2H, OU2.5, BTTS, H2HH1 (1st-half), AsianHandicap, DoubleChance, TT...
  "selection": "Draw",              // the actual bet: "Draw", "Over", "Yes", team name, etc.
  "line": null,                     // numeric line for OU/AH markets; null for H2H/BTTS
  "score": 32.43,                   // ⚠️ low scale — NOT comparable to NBA's 0-100/≥63
  "rating": "Good",                 // Good | Marginal | Weak  (driven by edge, not score)
  "odds": 3.86,                     // best available decimal odds
  "bestBookmaker": "pinnacle",      // Pinnacle is the sole model reference
  "edge": 0.32,                     // ← HEADLINE METRIC: modelProb − impliedProb (0.32 = +32%)
  "cappedEdge": 0.32,
  "fairOdds": 1.72,                 // model's fair price
  "modelProbability": 0.58,         // model's win prob
  "impliedProbability": 0.25,       // book's implied prob
  "closingImpliedProb": 0.2597,
  "isLive": true,                   // true = live pick; false = preview/backtest
  "scoringPass": "PM",              // AM (morning) | PM (near-tip, lineup-aware)
  "scoredWithLineups": false,
  "dataQualityScore": 1,            // 0-1
  "isPreview": false,
  "isLocked": true,
  "publicationStatus": "Research",  // Research | Published ... (Good public picks = Published)
  "isPublicPick": false,
  // ── 7 scoring blocks (each Score 0-100, Confidence 0-1) ──
  "formScore": 91.19,    "formConfidence": 0.9,
  "h2HScore": 50,        "h2HConfidence": 0,
  "strengthScore": 50,   "strengthConfidence": 0,
  "homeAwayScore": 50,   "homeAwayConfidence": 0,
  "goalsScore": 33.71,   "goalsConfidence": 0.85,
  "marketScore": 50,     "marketConfidence": 0,
  "contextScore": 58,    "contextConfidence": 0.5,
  "blockWeights": {},
  "blockDetails": [                 // sub-signals, e.g.
    { "name": "PoissonGoals", "probability": 0.337, "confidence": 0.85, "weight": 0 }
  ],
  "narrativeJson": "{\"summary_en\":\"...\",\"summary_es\":\"...\",\"source\":\"...\",\"generatedAt\":\"...\"}",
  "correlationGroupId": null, "correlationGroupName": null,
  "teamName": null, "result": null, // result set after settlement
  "version": 2
}
```

### `narrativeJson` (parse the string)
```jsonc
{
  "summary_en": "West Ham's recent form is exceptional—they're playing like a top-four side right now—and that's the real story here... The draw at 3.86 offers 32% edge over the Pinnacle line...",
  "summary_es": "West Ham está en una forma excepcional en estos momentos—juegan como un equipo de top cuatro...",
  "source": "...", "generatedAt": "..."
}
```
**Tweet copy:** use `summary_es` for La Liga picks, `summary_en` for everything else. Trim to fit 280 chars.

> **Tweet-relevant fields:** `homeTeam`/`awayTeam`, `league`, `market`, `selection`, `odds`, `edge`, `rating`, `kickoffUtc`, `modelProbability` vs `impliedProbability`, and the right `narrativeJson` summary. Filter: `rating == "Good"` + `edge >=` your threshold (e.g. 0.03), `isLive == true`.

---

## Track record (`flab_track_record`)

> Verified live in-session 2026-05-29. The MCP tool returns a **much richer payload** than the bare HTTP endpoint — full breakdowns by month, market, league, rating, plus a settled `picks[]` array. ⚠️ It's large and **truncates at ~40K chars** — narrow with `from`/`to`/`league`/`market` filters when you need the `picks[]` tail; the summary/breakdown blocks come first and are always intact.

```jsonc
{
  "summary": { "totalPicks": 262, "hits": 93, "hitRate": 0.3549, "profit": 20.97, "roi": 0.0800 },
                                  // ⚠️ hitRate/roi are raw FRACTIONS → ×100 for display
  "daily":   [ { "date": "2026-04-07T00:00:00Z", "dayProfit": 0.91, "cumulativeProfit": 0.91,
                 "picksCount": 1, "hitsCount": 1, "winRate": 1 } /* one per day */ ],
  "monthly": [ { "year": 2026, "month": 4, "picks": 207, "hits": 76, "hitRate": 0.367,
                 "profit": 28.64, "roi": 0.138, "cumulativeProfit": 28.64 } ],
  "byMarket":[ { "group": "H2H",   "totalPicks": 157, "hits": 45, "hitRate": 0.287, "profit": 24.66, "roi": 0.157 },
               { "group": "OU2.5", "totalPicks": 78,  "hits": 37, "hitRate": 0.474, "profit": -4.53, "roi": -0.058 } ],
  "byLeague":[ { "group": "Champions League", "totalPicks": 8,  "hits": 5,  "hitRate": 0.625, "profit": 3.53,  "roi": 0.441 },
               { "group": "La Liga",          "totalPicks": 44, "hits": 18, "hitRate": 0.409, "profit": 10.44, "roi": 0.237 },
               { "group": "Ligue 1",          "totalPicks": 53, "hits": 15, "hitRate": 0.283, "profit": -9.81, "roi": -0.185 } ],
  "byRating":[ { "group": "Good", "totalPicks": 262, "hits": 93, "hitRate": 0.355, "profit": 20.97, "roi": 0.080 } ],
  "dailyByMarket": { "OU2.5": [ { "date": "...", "dayProfit": 0.91, "cumulativeProfit": 0.91 } ], "H2H": [ ... ] },
  "picks": [                       // ← settled picks with outcomes — for transparency recaps
    { "date": "2026-05-06T19:00:00Z", "homeTeam": "Bayern München", "awayTeam": "Paris Saint Germain",
      "league": "Champions League", "market": "H2HH1", "rating": "Good", "selection": "Away",
      "edge": 0.16, "fairOdds": 2.63, "hit": true, "profit": 3.44, "closingOdds": 4.53 }
    // ...newest first; `closingOdds` enables CLV (closing-line-value) framing
  ]
}
```

Filters (AND-combined): `market`, `league`, `rating`, `outcome` (Won/Lost/Push), `from`, `to`, `isLive`.

> **Transparency framing = ROI, NOT hit rate.** Good picks hit only 35.5% but return **+8% ROI** — correct for a value model betting longer odds. The opposite framing from NBA props (where hit rate is the hook).
> **`byLeague` powers "ROI by league" tweets** — e.g. *Champions League +44% ROI, La Liga +24%, Ligue 1 −18.5%*. **`picks[]`** powers settled-result recaps (real outcomes + `closingOdds` for CLV). Both come straight from this one call.

---

## Matches (`flab_matches_today`, `flab_matches_upcoming`)

```jsonc
{
  "id": 2381,
  "homeTeam": "Nice", "awayTeam": "Saint Etienne",
  "homeTeamShort": "NIC", "awayTeamShort": "SAI",
  "homeTeamLogo": "...", "awayTeamLogo": "...",
  "league": "Ligue 1", "season": "2025",
  "matchday": null, "round": "Final",
  "kickoffUtc": "2026-05-29T18:45:00Z",
  "status": "Scheduled",            // Scheduled | Live | Finished
  "homeScore": null, "awayScore": null,
  "picks": [ /* embedded pick objects, same shape as above */ ]  // matches/today only
}
```
- `flab_matches_today` includes embedded `picks[]`; `flab_matches_upcoming` is schedule-only (use for the **Friday weekend-preview thread**, `days=3`).

---

## Markets seen live

`H2H` (1X2) · `H2HH1` (1st-half 1X2) · `OU2.5` (over/under 2.5 goals) · `BTTS` (both teams to score) · `AsianHandicap` · `DoubleChance` · `TT` (team totals). Real board (2026-04-10, 23 picks): H2H 12, BTTS 6, OU2.5 5 — by rating: Good 14, Marginal 1, Weak 8.

---

## Daily routine field mapping (vs NBA)

| Concept | NBA (proplab) | Football (footballlab) |
|---------|---------------|------------------------|
| Pick list | `proplab_dashboard.topPicks` | `flab_picks_today` / `flab_picks_board` |
| Filter | `rating=="Good"` & `scoreFinal>=63` | `rating=="Good"` & `edge>=0.03` (NOT score) |
| Headline metric | score /100 | **edge %** (model vs Pinnacle implied) |
| Narrative | `summary` (Spanish only) | `narrativeJson.summary_en` / `summary_es` |
| Results | `proplab_track_record` (percent fields) | `flab_track_record` (fraction fields) |
| Transparency hook | hit rate 63.2% (Good) | **ROI / profit** (hit rate is low by design) |
| Schedule | `proplab_games` | `flab_matches_today` / `flab_matches_upcoming` |
| Blocks | PlayerProfile, Matchup, Synergy, GameContext, MarketLine, AnalysisQuality, ExternalSignals | Form, H2H, Strength, HomeAway, Goals, Market, Context |
