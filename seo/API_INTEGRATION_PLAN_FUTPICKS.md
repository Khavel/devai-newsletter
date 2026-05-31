# FutPicks / FootballLab — Integration Plan for Twitter Automation (@FutProbLab)

> **Account:** @FutProbLab
> **Status (2026-05-29):** ✅ Integration path resolved. The `footballlab` MCP server is **built, registered, and verified** (boots over stdio, lists 17 tools, live API returns real data). Schema discovery is **done** — see `API_SCHEMAS_FUTPICKS.md`.
> **Primary path:** `footballlab` MCP tools (`mcp__footballlab__flab_*`) — 9 public tools, **no auth** needed for daily content.
> **Restart required:** MCP servers load at Claude Code startup. The `flab_*` tools appear after a restart.
> **Language:** Bilingual — `summary_es` for La Liga, `summary_en` for PL/CL/international.

---

## TL;DR — what changed

1. The football MCP existed on disk (`Furbov2\mcp-server`, "footballlab-mcp-server") but was **never registered** in `.claude.json`. Now it is, mirroring `proplab`.
2. Picks are exposed via `flab_picks_today` / `flab_picks_board` — **public, no auth**, like the NBA dashboard.
3. **Edge is the headline metric, not score.** Football "Good" picks have low raw scores (e.g. 32.43); the rating is edge-driven. Filter on `rating` + `edge`, never a score threshold.
4. **Narratives are bilingual and ready** — `narrativeJson.summary_en` / `summary_es`. No need to hand-write copy or translate.
5. **Transparency hook is ROI/profit, not hit rate** — the value model bets longer odds, so hit rate is low by design (~35%) while ROI is positive (+8%).
6. No token needed to ship. `FUTPICKS_API_KEY` only unlocks history/backtest/evaluate tools (optional).

---

## Integration path: footballlab MCP

| Need | Tool | Auth | Key fields |
|------|------|------|-----------|
| Pre-flight health | `flab_health` | public | status |
| Today's picks | `flab_picks_today` (default Good) | public | pick objects |
| Filtered board | `flab_picks_board` (edge/odds/rating/league) | public | pick objects |
| Pick deep-dive | `flab_pick_details` | public | blocks + `narrativeJson` |
| Today's matches | `flab_matches_today` | public | matches + embedded picks |
| Match + intelligence | `flab_match_details` | public | form/H2H/context snapshot |
| Weekend preview | `flab_matches_upcoming` (days=3) | public | upcoming fixtures |
| Results / ROI | `flab_track_record` | public | `summary` + `daily` |
| On-demand scoring | `flab_evaluate_match` | **Pro** | full block breakdown |
| Backtests | `flab_backtest_run` | **Pro** | win rate, ROI, breakdowns |

> Full response schemas with every field: **`API_SCHEMAS_FUTPICKS.md`**.

---

## Daily routine flow (API-direct via MCP)

```
0. flab_health → if unhealthy, pivot to educational, skip picks.
1. flab_matches_today → any matches today?
   - none → educational/methodology tweet → done
2. flab_picks_today (rating=Good)  [or flab_picks_board with minEdge filter]
   - Filter: rating == "Good", isLive == true, edge >= 0.03
   - none Good → top Marginal with softer framing, or educational
   - Sort by edge descending; take top 2-3
3. For each top pick: parse narrativeJson → pick summary_es (La Liga) or summary_en (others).
   Optionally flab_match_details(matchId, includeIntelligence=true) for thread context.
4. Build tweet (see template). Post via twitter_api_post.py --account FutProbLab, 2-4h spacing.
5. Friday → flab_matches_upcoming(days=3) + board → weekend preview thread (top edges Sat/Sun).
6. flab_track_record(isLive=true) → results recap (ROI-led). Post morning slot.
```

### Bilingual logic
- **La Liga** picks → Spanish (`summary_es`), `#LaLiga` hashtags.
- **Premier League / Champions League / international** → English (`summary_en`).
- **Results recap & weekend thread** → English (wider audience), flag emojis per league.

### Edge filtering (NOT score)
- Football scores run low and aren't comparable to NBA. Use `rating == "Good"` AND `edge >= 0.03` (3%).
- Sort tweet candidates by `edge` desc. `edge` is `modelProbability − impliedProbability`.

### Error / empty handling
- MCP error / `flab_health` down → educational content (never skip silently).
- Empty Good picks → "model still scoring" note or educational pillar.
- AM scoring pass (`scoringPass == "AM"`, `publicationStatus == "Research"`) = provisional; prefer PM/lineup-aware picks near kickoff.

---

## Tweet templates (English copy from real fields)

### Single pick
From `homeTeam`/`awayTeam`, `league`, `market`, `selection`, `odds`, `edge`, `modelProbability`/`impliedProbability`, `narrativeJson`.

```
⚽ Premier League — West Ham vs Wolves
Pick: Draw @ 3.86 (Pinnacle)

Model: 58% to draw vs 25% implied
Edge: +32% | Rating: Good

West Ham's form is exceptional right now — value is on the draw.

#PremierLeague #FootballBetting
```

> Map markets to readable labels: `H2H`→Match Result, `OU2.5`→Over/Under 2.5, `BTTS`→Both Teams To Score, `H2HH1`→1st-Half Result, `AsianHandicap`→AH, `DoubleChance`→Double Chance. Lead with the league + fixture; the `selection` + `odds` + `edge` are the core.

### La Liga pick (Spanish, from summary_es)
```
⚽ LaLiga — Barcelona vs Sevilla
Apuesta: Over 2.5 @ 1.95

Modelo: 61% vs 51% implícito
Edge: +10% | Rating: Good

[summary_es trimmed]

#LaLiga #ApuestasDeportivas
```

### Weekend preview thread (Fridays)
`flab_matches_upcoming(days=3)` + `flab_picks_board` → top edges across leagues, sorted by `edge`.
```
🏆 Weekend Preview 🧵
Top edges across Europe this weekend:

1/ 🏴 West Ham–Wolves — Draw (+32%)
2/ 🇪🇸 Barça–Sevilla — O2.5 (+10%)
3/ 🇮🇹 Inter–Roma — BTTS (+8%)
...
Full model card 👇
```

### Results / transparency recap (ROI-led)
From `flab_track_record.summary` (remember `hitRate`/`roi` are fractions → ×100).
```
📊 Model track record (live picks):
262 picks · +20.97 units · ROI +8.0%

Value betting means longer odds + lower hit rate by design.
The edge is in the price, not the win count.

#FootballBetting #ValueBetting
```

---

## Pick card images (Phase 2)

Pick objects carry `homeTeamLogo`/`awayTeamLogo` (api-sports CDN) + the 7 block scores (Form, H2H, Strength, HomeAway, Goals, Market, Context). Render a card or radar from those. Text-only ships first.

---

## Optional: Pro/Ops tokens

Add to the `footballlab` env in `.claude.json` to unlock the gated tools:
```json
"footballlab": {
  "command": "node",
  "args": ["C:\\Users\\ceja_\\Desktop\\Desarrollos\\Furbov2\\mcp-server\\dist\\index.js"],
  "env": {
    "FUTPICKS_API_URL": "https://futpicks.com",
    "FUTPICKS_API_KEY": "<Pro JWT>",       // unlocks history/backtest/evaluate/export/catalog
    "FUTPICKS_OPS_TOKEN": "<Admin JWT>"     // unlocks pipeline ops (not needed for Twitter)
  }
}
```
The public tools cover all Twitter content, so tokens are optional.

---

## Rating tiers & blocks

- **Ratings:** Good · Marginal · Weak (edge-driven). Tweet **Good** (occasionally top Marginal).
- **7 blocks:** Form, H2H, Strength, HomeAway, Goals, Market, Context — each `*Score` (0-100) + `*Confidence` (0-1). Plus `blockDetails[]` sub-signals (e.g. `PoissonGoals`).
- **Odds reference:** Pinnacle (`bestBookmaker: "pinnacle"`), the sole model comparison.

---

## Testing checklist

- [x] `footballlab` MCP registered in `.claude.json` (valid JSON)
- [x] Server boots over stdio; lists 17 tools
- [x] Live public API returns real data (picks/board, matches/today, track-record)
- [ ] **Restart Claude Code** → `mcp__footballlab__flab_*` tools available in session
- [ ] `flab_picks_today` filter: rating==Good & edge>=0.03 & isLive
- [ ] Bilingual routing: La Liga → summary_es, others → summary_en
- [ ] Track-record fields scaled correctly (hitRate/roi ×100 for display)
- [ ] ROI-led transparency framing (not hit-rate)
- [ ] Friday weekend-preview thread from flab_matches_upcoming
- [ ] `--dry-run` pick tweet + recap reviewed; lengths < 280
- [ ] Fallback to educational when slate empty / model still scoring
