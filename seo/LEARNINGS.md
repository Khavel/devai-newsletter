# SEO & Backlink Strategy Learnings -- DevAI Semanal

> Everything we learned building the backlink profile for devaisemanal.com from zero.
> Started: 2026-05-25 | Authority Score: 2 | Keywords: 14 | Backlinks: 20

---

## 1. The Newsletter Directory Ecosystem Is Mostly Dead

Of the ~20 newsletter directories we investigated, **more than half are dead, hijacked, or useless**:

| Status | Count | Examples |
|--------|-------|---------|
| Working & accepting submissions | 7 | InboxReads, LetterList, Rad Letters, StackLetter, Find Your Newsletter, Paved, Reletter |
| Dead / domain for sale | 4 | InboxStash, Newsletters.co, Newsletterest, Duuce |
| Hijacked by spam | 1 | Thanks for Subscribing (now a casino site) |
| Not actually directories | 3 | NewsletterHunt (RSS reader), Letterstack (blog), Email Love (design gallery) |
| Broken / temporarily down | 2 | Newsletry (error page), PostApex (signup broken) |
| Auto-index only (no submit form) | 1 | Reletter |
| Gated behind payment/long queue | 1 | Find Your Newsletter (183-day free queue) |

**Lesson**: Don't trust listicles of "50 best newsletter directories." Most are outdated. Validate every URL before starting any submission work. Budget 5 minutes per directory just for triage.

---

## 2. GitHub Awesome-Lists Are the Highest-ROI Backlink Source

GitHub (DA 96) gives **dofollow** links from README files. We submitted 6 PRs in one session:

| Repo | Stars | PR | Status |
|------|-------|----|--------|
| zudochkin/awesome-newsletters | 4K+ | #332 | Open |
| alternbits/awesome-ai-newsletters | ~200 | #39 | Open |
| jondot/awesome-weekly | ~600 | #56 | Open |
| jackbridger/developer-newsletters | ~100 | #31 | Open |
| gokulkrishh/awesome-web-newsletters | ~100 | #8 | Open |
| finxter/curated-list-of-ai-newsletters | 30+ | #5 | Open |

**Key learnings**:
- **Match the exact format** of the existing list. If entries use `- [Name](url) - Description`, don't add extra fields or emoji. PRs that break the pattern get rejected.
- **Fork first**, create a branch, make a minimal change, submit the PR with a short description explaining what the newsletter is and why it belongs.
- **Check for forks**: wallies/awesome-newsletters is a fork of zudochkin. Submitting to both is redundant -- the fork will eventually sync from upstream.
- **One PR per repo**. Don't bundle multiple changes.
- These can take weeks to merge. Some maintainers are inactive. It's a numbers game -- submit to many, expect some to land.

---

## 3. SEMrush Metrics Explained (What They Mean at Our Scale)

### Current snapshot (May 2026):
```
Authority Score:     2    (scale 0-100, we're at the very bottom)
Organic Keywords:   14    (queries where we appear in Google's top 100)
Organic Traffic:     2    (estimated monthly visits from organic search)
Backlinks:          20    (total links pointing to us)
Referring Domains:  19    (unique websites linking to us)
Dofollow Links:      0    (ZERO -- this is the critical problem)
```

### What each metric means:

**Authority Score (AS)**: SEMrush's composite score based on backlinks, organic traffic, and spam signals. AS 2 means we're brand new with minimal signals. For context: major sites are 80-100, good niche sites are 30-50, new sites start at 0-5.

**Organic Keywords**: The number of keywords where devaisemanal.com appears anywhere in Google's top 100 results. Going from 0 (March) to 2 (April) to 14 (May) is a strong growth signal -- Google is discovering and indexing our content pages.

**Organic Traffic**: SEMrush's *estimate* based on keyword positions and click-through rates. At position #20 for "cursor ai" (8,100 volume), SEMrush estimates ~1% CTR = ~2 visits. Real traffic from Search Console will be higher because SEMrush can't see all long-tail queries.

**Referring Domains vs Total Backlinks**: 19 domains producing 20 links = a 1:1 ratio, which is healthy. A ratio like 5 domains producing 500 links would scream "spam." Google values domain diversity over raw link count.

**Dofollow vs Nofollow**: All 20 current backlinks are nofollow. Nofollow tells Google "don't pass link equity." This means our links currently provide zero direct ranking benefit. The directory and GitHub PR campaign specifically targets dofollow links to fix this.

### Growth trajectory:
```
March 2026:  0 keywords, 0 traffic (site invisible to Google)
April 2026:  2 keywords, 0 traffic (first pages indexed)
May 2026:   14 keywords, 2 traffic (guide pages climbing)
```

**Lesson**: This 0-to-14 keyword growth in two months is actually fast for a brand-new domain with no backlink authority. The content is good -- what's holding us back is link authority (AS 2, zero dofollow links).

---

## 4. Keyword Positioning Analysis

Our top-performing keywords in Spain (ES database):

| Keyword | Position | Monthly Volume | Page |
|---------|----------|---------------|------|
| cursor ai | #20 | 8,100 | /cursor-ai-que-es-guia-completa/ |
| codewhisperer ia | #22 | 110 | /amazon-codewhisperer-vs-q-developer/ |
| cursor open ai chat | #23 (NEW) | 40 | /cursor-ai-que-es-guia-completa/ |
| bolt.new | #32 | 1,900 | /bolt-new-crear-apps-ia-navegador/ |
| replit | #37 | 14,800 | /replit-programar-navegador-ia/ |
| bolt new | #38 | 1,900 | /bolt-new-crear-apps-ia-navegador/ |
| replt (typo) | #42 | 480 | /replit-programar-navegador-ia/ |
| mcp | #51 | 8,100 | /mcp-model-context-protocol-guia/ |

**Key observations**:
- **"cursor ai" at #20 is the biggest opportunity.** Volume 8,100 and we're right at the edge of page 2. Moving to page 1 (top 10) would 5-10x the traffic from this keyword alone. CTR jumps from ~1% at position 20 to ~5-10% in positions 3-7.
- **"replit" at #37 has the highest volume (14,800)** but we're on page 4 -- too deep for meaningful traffic. This would require significant authority growth.
- **"mcp" at #51 (volume 8,100)** is promising but the keyword is ambiguous (MCP = many things). The long-tail "model context protocol" or "mcp server" would be better targets.
- **Typo keywords work**: "replt" (#42) and "replyit" (#44) rank because competitors don't optimize for misspellings.
- **All traffic goes to guide/pillar pages**, not newsletter issues. This confirms the strategy: write comprehensive evergreen guides, link to them from weekly issues.

**Lesson**: Focus on pushing "cursor ai" from #20 to top 10. Internal linking, content updates to that page, and backlinks pointing to /cursor-ai-que-es-guia-completa/ specifically would have the highest ROI.

---

## 5. The Canonical URL Strategy (Dev.to + Ghost)

We published a technical article on Dev.to with a canonical URL pointing back to devaisemanal.com:

```
Dev.to article: /como-automatice-una-newsletter-de-ia-para-developers-con-claude-api-y-github-actions
    canonical_url -> https://devaisemanal.com/como-automatice-newsletter-ia-developers/

Ghost page: /como-automatice-newsletter-ia-developers/
    (created via Ghost Admin API using create_canonical_page.py)
```

**How it works**: When Dev.to has `canonical_url` set, Google treats the canonical (our Ghost page) as the "real" source. Dev.to's DA ~60 passes partial link equity to our domain. The Dev.to article gets Dev.to community traffic; the SEO value flows back to us.

**Technical detail**: The Ghost page was created as a `post` (not a `page`) because Ghost posts get indexed in sitemaps and have tags, while Ghost pages don't. The `create_canonical_page.py` script handles JWT auth against the Ghost Admin API.

**Lesson**: Cross-posting with canonical URLs is free, reversible, and compounds over time. Do this for every long-form article.

---

## 6. Disavow File: Cleaning Up Spam Backlinks

We uploaded a disavow.txt to Google Search Console with 19 spam domains:

```
# Example entries from disavow.txt:
domain:spamsite1.com
domain:spamsite2.com
...
```

**Why**: Even a brand-new site can accumulate spam backlinks from scraper sites and negative SEO. Google's algorithm may penalize sites with spammy backlink profiles. The disavow file tells Google "ignore these links."

**Lesson**: Check backlinks monthly. New spam domains appear constantly. A clean backlink profile is especially important for new sites that don't have enough "good" links to dilute the bad ones.

---

## 7. Platform-Specific Submission Gotchas

### Product Hunt
- Newsletters qualify as products. Create a proper launch page with tagline, description, and screenshots.
- Schedule launches for Tuesday-Thursday (highest engagement).
- The backlink (DA 91, dofollow) is permanent regardless of upvote count.

### Paved
- Multi-step onboarding: topic dropdown requires scrolling to find "Tech", frequency selection, impressions input.
- Creates a publisher profile that doubles as a sponsorship marketplace listing.

### AlternativeTo
- **7-day account age requirement** for new submissions. You can't submit on the same day you create an account.
- Cloudflare CAPTCHA blocks automated signups -- had to create account manually.
- List as alternative to existing newsletters (TLDR, The Rundown, etc.)

### Crunchbase
- Requires linking Google or LinkedIn social auth BEFORE you can create any organizations.
- After linking, there's a manual review period (up to 1 business day).
- DA 91, dofollow -- one of the highest-value backlinks available.

### G2
- User accounts (for reviews) are separate from product/vendor listings.
- Product listings require the seller portal at sell.g2.com with its own auth flow.
- DA 91, dofollow on product pages.

### Indie Hackers
- Tag-style button selectors for categories (not dropdowns). Tags have different background colors by category -- blue for selected, red/pink for some tag groups. Don't confuse color coding with selection state.
- File upload for logo opens a native picker -- can't be automated if the file isn't in the browser session's shared files.
- Screenshot timeouts are common (CDP captureScreenshot times out after 30s).

### Find Your Newsletter (Tally.so form)
- First attempt: page stuck loading for 45+ seconds due to bot detection. Succeeded on retry in a fresh tab group.
- 4-step form: basic info -> description/category/tags -> logo/banner (optional) -> payment (optional) + reCAPTCHA + submit.
- **183-day free queue**. $19.99 to skip it. Unless you're in a hurry, the free queue is fine.

### LetterList (Airtable form)
- Embedded Airtable form on /submit. Straightforward -- name, URL, description, email.
- Confirmation message appears inline: "Thanks for contributing - you absolute legend, you!"

---

## 8. Bot Detection & Automation Limits

### What triggers bot detection:
- **Tally.so**: Aggressive bot detection. Page refuses to load (stuck on "document_idle" for 45+ seconds) when accessed via automated browser. Worked on second attempt after creating a fresh tab group.
- **Cloudflare CAPTCHA**: AlternativeTo uses Cloudflare's bot mitigation. Completely blocks automated form filling. Required manual account creation.
- **reCAPTCHA**: Find Your Newsletter's final step has reCAPTCHA v2. Surprisingly, it passed on first click even through browser automation (Chrome MCP). Not reliable -- expect failures.

### What works fine with automation:
- Simple HTML forms (InboxReads, StackLetter, Rad Letters)
- Airtable embedded forms (LetterList)
- GitHub PR creation via `gh` CLI
- Ghost Admin API (programmatic page creation)

### Chrome MCP limitations:
- **File uploads**: Can only upload files from the browser session's shared files directory. Local filesystem files (`C:\Users\...`) are rejected. Workaround: user must upload manually.
- **Screenshot timeouts**: Some heavy SPAs (Indie Hackers) cause CDP `Page.captureScreenshot` to timeout after 30 seconds. Retry as standalone call usually works.
- **Tab group persistence**: Tab groups can be lost between conversation contexts. Always call `tabs_context_mcp` first to check.

**Lesson**: Automate what's easy (APIs, simple forms, GitHub CLIs), accept that heavy CAPTCHAs and file uploads need human intervention. Don't waste time fighting bot detection -- just note it and move on.

---

## 9. Link Velocity Matters

Google's algorithm monitors how fast you acquire backlinks. A brand-new site that suddenly gets 50 backlinks in a day looks unnatural. Our approach:

```
Week 1:  ~15 submissions (directories + GitHub PRs + Dev.to)
Week 2:  ~4 submissions (AlternativeTo, Crunchbase, G2, Product Hunt launch)
Week 3-4: Outreach emails (naturally slower response rate)
Week 5+:  Follow-ups and new opportunities
```

This creates a natural-looking velocity: a burst of initial setup, tapering to steady growth. The GitHub PRs especially help because they merge at different times over weeks, spacing out the actual link creation.

**Lesson**: Front-load the easy submissions, space out the rest. Never buy links or use link farms -- with AS 2, any spam signal could tank the site.

---

## 10. Content Strategy: Guides Beat Newsletter Issues

SEMrush data confirms: all 14 ranking keywords point to **guide/pillar pages**, not to individual newsletter issues:

```
/cursor-ai-que-es-guia-completa/          -> 3 keywords
/replit-programar-navegador-ia/           -> 3 keywords
/bolt-new-crear-apps-ia-navegador/        -> 3 keywords
/mcp-model-context-protocol-guia/         -> 1 keyword
/github-copilot-guia-completa/            -> 2 keywords
/amazon-codewhisperer-vs-q-developer/     -> 1 keyword
/v0-dev-generar-ui-ia/                    -> 1 keyword
```

**Why**: Guide pages are evergreen, comprehensive, and target high-volume informational queries. Newsletter issues are ephemeral and target no specific keyword.

**Strategy**: Write a definitive guide for each AI developer tool (in Spanish), optimize it for the tool's brand name + "que es" / "guia" queries, and use weekly newsletter issues to drive internal links back to the guides.

**Lesson**: The newsletter is the distribution channel. The guides are the SEO assets. Build both.

---

## 11. Spanish-Language SEO Advantage

Competing in Spanish gives us a structural advantage:

- **Less competition**: "cursor ai" in Spanish Google has far fewer competing pages than in English.
- **Underserved market**: Most AI tool guides are English-only. A high-quality Spanish guide often ranks in the top 20 purely because there's nothing else.
- **Position #20 for 8,100-volume keyword** would be nearly impossible for a new English-language site competing against established publications.

**Trade-off**: Lower total addressable search volume (Spanish-speaking developers < English-speaking), but much easier to rank and dominate the niche.

**Lesson**: If you're building in a non-English language, you're playing the game on easy mode for SEO. The flip side is smaller ceiling -- but for a newsletter, owning the niche is more valuable than fighting for scraps in a saturated market.

---

## 12. What's Next: The Roadmap to AS 20+

Based on everything we've learned, here's the path from AS 2 to AS 20+:

### Short-term (Weeks 1-4, targeting AS 5-8):
- [x] Submit to all viable directories (done)
- [x] Submit GitHub PRs for dofollow links (done)
- [x] Publish Dev.to article with canonical (done)
- [ ] Product Hunt launch (scheduled May 26)
- [ ] Complete AlternativeTo, Crunchbase, G2 submissions
- [ ] Start Tier 5 editorial outreach

### Medium-term (Months 2-3, targeting AS 10-15):
- [ ] Push "cursor ai" from #20 to top 10 (content update + internal linking + targeted backlinks)
- [ ] Write 3-5 new tool guides for emerging AI coding tools
- [ ] Guest post on 2-3 Spanish-language tech blogs
- [ ] Consider Substack mirror for DA 93 backlink + discovery feed exposure
- [ ] Follow up on all pending GitHub PRs

### Long-term (Months 4-6, targeting AS 15-20):
- [ ] Consistent weekly content with internal linking to guide pages
- [ ] Monthly backlink monitoring and disavow updates
- [ ] HARO / Connectively responses for journalist mentions
- [ ] Conference/meetup mentions (Spanish developer events)
- [ ] Build relationships with other newsletter creators for cross-promotion

### Metrics to track monthly:
```
SEMrush:
  - Authority Score (target: +3-5 points/month)
  - Organic Keywords (target: +10-20/month)
  - Referring Domains (target: +5-10/month)
  - Dofollow ratio (target: >30% dofollow)

Google Search Console:
  - Total impressions
  - Total clicks
  - Average position for "cursor ai"
  - New backlinks discovered

Ghost/MailerLite:
  - Subscriber count
  - Open rate
  - Click rate
```

---

## Appendix: Tools Used

| Tool | Purpose | Notes |
|------|---------|-------|
| SEMrush API (via MCP) | Domain analysis, keyword tracking, backlink overview | 10-40 API units per report |
| Ghost Admin API | Creating canonical pages programmatically | JWT auth, `create_canonical_page.py` |
| GitHub CLI (`gh`) | Forking repos, creating PRs for awesome-lists | Fastest way to submit PRs |
| Chrome MCP (Claude in Chrome) | Automating form submissions on directory sites | Good for simple forms, fails on heavy CAPTCHAs |
| Google Search Console | Disavow file upload, indexing status | Manual upload for disavow.txt |
| Dev.to | Cross-posting with canonical URL | Set `canonical_url` in article frontmatter |

---

*Last updated: 2026-05-25*
