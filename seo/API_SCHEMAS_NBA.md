# NbaPropLab — Real MCP Response Schemas (Ground Truth)

> **Source:** Captured live from the `proplab` MCP server on 2026-05-28.
> **Purpose:** Authoritative field reference for the @StatLineNerd Twitter automation. The OpenAPI docs at docs.nbaproplab.com document endpoints/params but NOT response bodies (all show `200 OK` only). These are the **real** structures.
> **Integration path:** Use the `proplab` MCP tools directly — they are live and reliable. `proplab_dashboard` and `proplab_track_record` are **public (no auth)**.

---

## ⚠️ Season context (as of late May 2026)

The model scores **both NBA and WNBA**. In late May the NBA is down to the Finals (1 game/night) while the **WNBA season is in full swing** — so almost all "Good" picks right now are WNBA. The routine must handle both leagues. The `league` field on every pick is `"Nba"` or `"Wnba"`.

---

## Tool: `proplab_dashboard`  (public, no auth)

Params: `date` (YYYY-MM-DD, default today CST), `league` (`nba` | `wnba`, optional).

```jsonc
{
  "date": "2026-05-28",
  "gamesCount": 3,
  "picksCount": 486,
  "topPicks": [                       // top 10 by scoreFinal
    {
      "id": 378834,                   // pick ID → use with proplab_pick_details
      "playerId": 704,
      "playerName": "Paige Bueckers",
      "teamAbbreviation": "DAL",
      "opponentAbbreviation": "LVA",
      "stat": "RebAst",               // Points|Rebounds|Assists|Threes|PtsRebAst|PtsReb|PtsAst|RebAst...
      "line": 8.5,
      "direction": "Over",            // Over | Under
      "scoreFinal": 65,               // 0-100 confidence score
      "rating": "Good",               // Good | Marginal | Weak | Avoid (Elite possible, rare)
      "ratingEmoji": "🔥",            // 🔥 Good · ✅ Marginal
      "summary": "🔥 Pick premium — Paige Bueckers: R+A por encima de 8.5\nPuntos fuertes: ...",
                                       // PRE-WRITTEN Spanish summary, ready to drop into a tweet
      "blockScores": [                // 7 blocks, each: blockName, score, confidence
        { "blockName": "Matchup",         "score": 50.8, "confidence": 0.3 },
        { "blockName": "Synergy",         "score": 61.7, "confidence": 0.5 },
        { "blockName": "MarketLine",      "score": 66.4, "confidence": 0.65 },
        { "blockName": "GameContext",     "score": 55.4, "confidence": 0.7 },
        { "blockName": "PlayerProfile",   "score": 63.3, "confidence": 0.8 },
        { "blockName": "AnalysisQuality", "score": 84.1, "confidence": 0.888 },
        { "blockName": "ExternalSignals", "score": 52.5, "confidence": 0.35 }
      ],
      "isVoided": false,
      "isPeriodDataGap": false,
      "league": "Wnba",               // "Nba" | "Wnba"
      "l10Hits": 1,                   // hits in last-10 sample
      "l10Games": 5,                  // games in that sample (WNBA early season → small)
      "period": "FullGame"
    }
    // ... up to 10
  ],
  "ratingDistribution": { "elite": 0, "good": 7, "marginal": 34, "weak": 141, "avoid": 304 },
  "games": [
    {
      "id": 4251,
      "homeTeam": "San Antonio Spurs",
      "awayTeam": "Oklahoma City Thunder",
      "homeTeamAbbr": "SAS",
      "awayTeamAbbr": "OKC",
      "spread": -3.5,
      "total": 218.5,
      "status": "Scheduled",          // Scheduled | InProgress | Final ...
      "gameDate": "2026-05-28T00:00:00+00:00"
    }
  ]
}
```

**Tweet-relevant fields:** `playerName`, `teamAbbreviation`, `opponentAbbreviation`, `stat`, `line`, `direction`, `scoreFinal`, `rating`, `ratingEmoji`, `summary`, `league`, top `blockScores`.

---

## Tool: `proplab_track_record`  (public, no auth)

Params: `from`, `to` (YYYY-MM-DD), `league`, `tier` (`Good|Premium|Marginal|Standard`), `statType`.

```jsonc
{
  "totalPicksSettled": 29466,
  "totalHits": 16271,
  "totalMisses": 13195,
  "overallHitRate": 55.2,            // percent
  "totalProfit": 1611.6,             // units
  "totalDays": 83,
  "firstDate": "2026-01-01",
  "lastDate": "2026-05-27",
  "elitePicks":    { "picks": 0,    "hits": 0,    "misses": 0,    "hitRate": 0,    "profit": 0,     "avgScore": 0,    "roi": 0 },
  "goodPicks":     { "picks": 2820, "hits": 1783, "misses": 1037, "hitRate": 63.2, "profit": 585.5, "avgScore": 64.8, "roi": 20.8 },
  "marginalPicks": { "picks": 6210, "hits": 3676, "misses": 2534, "hitRate": 59.2, "profit": 811.2, "avgScore": 61.3, "roi": 13.1 },
  "weakPicks":     { "picks": 20436,"hits": 10812,"misses": 9624, "hitRate": 52.9, "profit": 214.9, "avgScore": 57,   "roi": 1.1 },
  "dailyResults": [                  // newest first
    { "date": "2026-05-27", "picksSettled": 163, "hits": 84, "misses": 79,
      "hitRate": 51.5, "profit": -2.6, "cumulativeProfit": 1611.6,
      "goodPicks": 0, "goodHits": 0, "isLive": true }
  ],
  "currentStreak": 1,
  "streakType": "losing",            // "winning" | "losing"
  "recentGoodPicks": [               // settled ones carry hit + actualValue
    { "date": "2026-05-27", "playerName": "Courtney Williams", "stat": "RebAst",
      "direction": "Over", "line": 8.5, "score": 66.7, "rating": "Good",
      "hit": true, "actualValue": 10, "isLive": true, "league": "Wnba" }
  ],
  "motorPicksDaily": [               // the curated daily top-10 ("motor") slate
    { "date": "2026-05-27", "totalPicks": 10, "hits": 5, "misses": 5, "hitRate": 50, "profit": -0.4 }
  ]
}
```

**Tweet-relevant fields for transparency tweets:** `overallHitRate`, `totalProfit`, `goodPicks.{hitRate,roi,picks}`, `dailyResults[0]` (yesterday), `recentGoodPicks` (with `hit`/`actualValue` for settled results), `currentStreak`/`streakType`.

> **Headline credibility stat:** Good picks = **63.2% hit rate, +20.8% ROI over 2,820 picks**. This is the strongest transparency hook for @StatLineNerd.

---

## Tool: `proplab_pick_details`  (params: `id`)

Returns the full pick incl. `finalSpider` (the 7-axis radar for image generation) and per-block `explanation` narratives (rich, pre-written Spanish).

```jsonc
{
  "id": 378714, "playerId": 330, "gameId": 4251,
  "playerName": "Keldon Johnson", "teamAbbreviation": "SAS", "opponentAbbreviation": "OKC",
  "stat": "PtsRebAst", "line": 11.5, "direction": "Over",
  "scoreFinal": 62.8, "rating": "Marginal", "ratingEmoji": "✅",
  "summary": "✅ Pick estándar — Keldon Johnson: PRA por encima de 11.5\nPuntos fuertes: ...",
  "createdAt": "2026-05-28T22:00:54Z",
  "finalSpider": {                   // ← spider chart image input (7 axes, 0-100)
    "name": "Overall",
    "axes": [
      { "label": "PlayerProfile",   "value": 57.9, "max": 100 },
      { "label": "Matchup",         "value": 58,   "max": 100 },
      { "label": "Synergy",         "value": 61.7, "max": 100 },
      { "label": "GameContext",     "value": 63.6, "max": 100 },
      { "label": "MarketLine",      "value": 69.4, "max": 100 },
      { "label": "AnalysisQuality", "value": 78.6, "max": 100 },
      { "label": "ExternalSignals", "value": 52.5, "max": 100 }
    ]
  },
  "blocks": [                        // each block: score, confidence, spider (sub-axes), explanation, subScores
    {
      "blockName": "MarketLine", "score": 69.4, "confidence": 0.87,
      "spider": { "name": "MarketLine", "axes": [ {"label":"EdgeVsLine","value":35,"max":100}, ... ] },
      "explanation": "El análisis de mercado está claramente a nuestro favor: proyectamos 18.7 PRA frente a la línea de 11.5 (+7.2). ... El valor esperado es positivo y atractivo (+56.0 %).",
      "subScores": { "EdgeVsLine": 35, "LineMovement": 55, "BookConsensus": 67, "ExpectedValue": 95, "ImpliedProbability": 95 }
    }
    // + AnalysisQuality, GameContext, Synergy, Matchup, PlayerProfile, ExternalSignals
  ],
  "period": "FullGame"
}
```

**Block sub-axes (for analysis threads / spider charts):**
- **PlayerProfile:** Trend, Fatigue, RoleUsage, SeasonAvg, Consistency, PlayTypeFit, ClutchCeiling, MinutesStability, TeammateContextFit, StarDependencyPenalty
- **Matchup:** DvP, H2H, Pace, DefRating, DefVsPlayType, DefVsShotType, RimProtection, ThreePointDef, SimilarPlayers
- **MarketLine:** EdgeVsLine, LineMovement, BookConsensus, ExpectedValue, ImpliedProbability
- **GameContext:** HomeAway, GameTotal, B2BFatigue, BlowoutRisk, RefereeImpact, RivalInjuries, GameImportance
- **Synergy:** UsageShift, InjuryImpact, HistoricalWithWithout
- **AnalysisQuality:** HitRate, WilsonCI, Divergence, SampleSize, Consistency, BayesianScore
- **ExternalSignals:** InsiderLeads, Tank01Projection, ExternalConsensus

> `subScoreDetails[].rawData` comes back empty in the MCP payload — use `subScores` for the numbers and `explanation` for the narrative.

---

## Tool: `proplab_games`  (params: `date`)

Same `games[]` shape as the dashboard's `games` array (id, homeTeam/awayTeam, abbrs, spread, total, status, gameDate). Use to decide whether @StatLineNerd posts at all.

---

## Other proplab tools (reference)

| Tool | Auth | Use |
|------|------|-----|
| `proplab_system_status` | public | Pipeline health, job runs, data freshness — pre-flight check |
| `proplab_search_players` | — | Resolve player name → playerId |
| `proplab_player_research` | — | Player deep-dive (game logs, trends) |
| `proplab_evaluate_pick` | **auth (PROPLAB_API_KEY)** | Score a custom pick on demand |
| `proplab_backtest_summary` | **auth** | Aggregate backtest (hit rate, ROI) for a range |
| `proplab_backtest_daily` | **auth** | Daily backtest breakdown |
| `proplab_backtest_by_rating` | **auth** | Backtest split by rating tier |
| `proplab_backtest_by_stat` | **auth** | Backtest split by stat type |

> The auth-gated tools need `PROPLAB_API_KEY` (created via `POST /api/v1/me/api-keys` on a Sharp-tier account). The public dashboard + track_record already cover daily tweet content, so the API key is **optional** — only needed for on-demand scoring and detailed backtests.

---

## Stat abbreviations used in summaries

`PTS` Points · `REB` Rebounds · `AST` Assists · `PRA`/`P+R+A` PtsRebAst · `P+R` PtsReb · `P+A` PtsAst · `R+A` RebAst · `3PT` Threes
