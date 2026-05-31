# GA4 ↔ Search Console linking — runbook (pending task)

**Status:** NOT done. The 3 GA4 properties have NO Search Console link yet
(each shows "Aún no hay vinculaciones"). This is the only remaining GA item.
It is **optional** — GA data collection + Search Console both already work
independently. Linking just surfaces organic-query reports *inside* GA.

**Why it's not in the API:** the GA4 Admin API does NOT expose
`searchConsoleLinks` (verified — only BigQuery/Google Ads link methods exist).
UI-only. Must be done via Chrome.

## Facts
- GA account: **Khavel Projects** (id `396315220`), logged in as **khavel112@gmail.com**.
- All 3 sites are verified in Search Console as **URL-prefix** properties:
  `https://devaisemanal.com/`, `https://nbaproplab.com/`, `https://futpicks.com/`
  (there is also a `tpv-top.com` Domain property and `https://nbaproplab.com/` —
  pick the exact matching URL-prefix per property).
- Property IDs:
  - DevAI Semanal → `539660132`  → SC `https://devaisemanal.com/`
  - NbaPropLab    → `539606177`  → SC `https://nbaproplab.com/`
  - FutPicks      → `539652295`  → SC `https://futpicks.com/`

## The wizard (repeat per property)
Start URL (opens the SC-links list for that property):
`https://analytics.google.com/analytics/web/#/a396315220p<PROPID>/admin/integrations/search-console`

1. Click **Vincular** (blue) → goes to `.../search-console/new`, 3-step wizard.
2. Step 1 "Elegir una propiedad de Search Console": click **Elegir cuentas**
   → in the picker table, **check the row whose URL matches this property's
   domain** → click **Confirmar** (top-right).
   - VERIFY the step-1 summary shows the correct domain before continuing.
   - The picker is "máximo 1": if a wrong one is pre-checked, UNCHECK it first.
3. Click **Siguiente** (under step 1).
4. Step 2 "Selecciona el flujo web": click **Seleccionar** → check the single
   web stream → **Confirmar** → **Siguiente**.
5. Step 3 "Revise y envíe": click **Enviar**.
6. Verify: the SC-links list now shows a row with the SC property + stream.

## ⚠️ CRITICAL automation lesson (why the first attempt failed)
The wizard is a modal that **rebuilds the DOM on every step**, so element
`ref_xxxx` IDs go STALE immediately after any click. What failed:
- Batching many clicks with pre-guessed refs → every action after the first
  errored ("element removed"), or clicked the wrong thing (opened the
  "Enviar comentarios" feedback panel, navigated away).

What WORKS:
- **One action per turn.** After EACH click, take a fresh `find` (or
  `read_page`) and use the ref it returns RIGHT NOW. Never reuse a ref across
  a DOM change. Never guess the next ref.
- Prefer `find` immediately before each click; screenshot to confirm state.
- Close the "Enviar comentarios a Google" side panel if it appears (X top-right
  ~1543,24) — a misclick on the footer "Enviar comentarios" opens it.
- For FutPicks especially: confirm **futpicks.com** is the selected SC property
  (an earlier attempt left devaisemanal.com pre-selected on the FutPicks
  property — would have cross-linked the wrong site).

## After linking (per property) — make reports visible
Linking alone doesn't surface the reports:
- **Informes** → **Biblioteca** (bottom-left of Reports) → find the
  **"Search Console"** collection → **⋮ → Publicar**.
Then "Search Console" (Queries / Google organic search) appears in the left nav.

## Verify (no API for SC links; GSC OAuth token is expired)
- Visual: each property's SC-links list shows 1 row.
- Or: after ~a day, the Search Console report in GA populates.
