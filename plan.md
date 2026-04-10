# SEO Improvement Plan — Everest (ecstudy.co.il)
**Analysis date:** 2026-04-10 | **GSC data window:** Jan 7 – Apr 7, 2026 (90d)

---

## Part 1: GSC Diagnosis — What the Data Shows

### Site-level numbers
| Metric | 90-day total | Last 28 days | Signal |
|---|---|---|---|
| Total clicks | 522 | 84 | **Traffic dropped ~50%** in last month |
| Total impressions | 16,981 | 1,967 | Visibility also declining |
| Avg position | 27.0 | — | Mostly page 3+ |
| Avg CTR | 1.77% | — | Below floor (industry ~2-3%) |
| Blog posts tracked | 33 | 21 | 12 posts dropped off GSC entirely |

**The 28d vs 90d split is the most alarming signal.** The monthly average implied by 90d is ~174 clicks/month. Last 28d was 84 — a 52% drop in a single month. This didn't happen gradually; something broke.

### Blog post health breakdown (90d)
| Category | Count | Meaning |
|---|---|---|
| top_performer | 3 | Working well — do NOT touch |
| page2_opportunity | 11 | Positions 11–30, impressions ≥ 20 — highest ROI |
| ctr_opportunity | 1 | Page 1 but not getting clicked |
| low_performer | 15 | GSC data exists but ranking position 30–70 |
| not_indexed | 3 | No GSC data at all |

### The 3 top performers (never modify these)
1. `/` — 312 clk, pos 7.1 (brand query "מכללת אוורסט")
2. `/programs/קורס-חיווט-חשמל` — 59 clk, pos 9.7
3. `/programs/קורס-נהג-רכב-חילוץ-וגרירה-היתר-103` — 40 clk, pos 4.9

### Page 2 opportunities (sorted by impressions — highest ROI)
| Page slug | Pos | Impr | Top query |
|---|---|---|---|
| קורס-רכב-ציבורי | 28.7 | 1,151 | מכללת אוורסט |
| קורס-נהיגת-רכב-משא-כבד-444... | 26.9 | 711 | מבחן נהיגה נכונה משא כבד |
| קורס-מורה-נהיגה | 30.0 | 620 | קורס מורה נהיגה |
| קורס-מלווה-הסעות | 15.1 | 288 | מלווה הסעות |
| קורס-מוביל-קצר | 21.0 | 282 | קורס רישיון מוביל |
| קורס-חומרים-מסוכנים-חומס-הכשרה... | 12.2 | 157 | חומרים מסוכנים |
| קורס-חומרים-מסוכנים-תעבורה-חומס | 21.3 | 152 | קורס חומרים מסוכנים |
| קורס-סולידוורקס | 16.7 | 116 | קורס solidworks |
| קורס-קריאת-תוכניות-בנייה | 16.2 | 102 | קורס קריאת תוכניות בנייה |

### Critical low performers (high impressions, terrible ranking)
| Page slug | Pos | Impr | Problem |
|---|---|---|---|
| קורס-נהג-אוטובוס-זעיר-ציבורי | 40.3 | 1,790 | Page 4, tons of visibility, zero conversions |
| קורס-הנהלת-חשבונות | 68.9 | 1,193 | Page 7, most-searched course, not ranking |
| קורס-מנהל-עבודה-בבניין | 31.1 | 832 | Page 3, high volume |
| קורס-מנהל-עבודה-הנדסאים-274 | 48.0 | 828 | Page 5, duplicate of above |
| קורס-קצין-בטיחות-בתעבורה | 31.9 | 591 | Page 3 |
| קורס-נהג-אוטובוס-זעיר-פרטי | 63.3 | 521 | Page 6+ |

---

## Part 2: Root Cause Analysis

### Problem A: Keyword Cannibalization — the single biggest damage
**104 queries** are being fought over by multiple pages. This is directly caused by the AI content generation creating duplicate content for the same courses.

Examples of cannibalization pairs:
- "קורס מנהל עבודה בבניין" → 3 different pages competing (pos 31, 48, 48)
- "קורס נהג אוטובוס" → 3 pages competing (pos 40, 63, 40)
- "קורס רכב ציבורי" → 2 pages competing (pos 28.7, 13.1)
- "קורס הנהלת חשבונות" → 5 pages competing (pos 68.9, 46.9, 64.3, 53.5, all bad)
- "קורס משא כבד" → 5 pages competing

When Google sees 5 pages on the same site targeting the same query, it doesn't rank all 5 — it often ranks none of them well because it can't tell which is canonical.

**Root cause in code:** The AI content generator creates new blog posts for topics already covered by existing course pages in the same CMS. The `_is_topic_covered_by_title()` check uses 60% Hebrew word overlap, which may not catch cases where existing course pages (product pages) already own a keyword.

### Problem B: AI-generated URL patterns are visible to Google
Many pages have AI-generated titles embedded in their URLs — extremely long, marketing-flavored slugs that no human would use:
- `קורס-רכב-ציבורי-במכללת-אוורסט-הצעד-הבא-בקריירה-שלך` (The next step in your career at Everest College)
- `קורס-חומרים-מסוכנים-תעבורה-חומס-הכשרה-מקצועית-במכללת-אוורסט`
- `קורס-הנהלת-חשבונות-12-במכללת-אוורסט-הצעד-הראשון-לקריירה-מצליחה`

Google's Helpful Content system and quality raters look at URLs. A clean URL like `/קורס-הנהלת-חשבונות` signals genuine page intent. A 10-word marketing phrase URL signals AI generation.

### Problem C: SERP snippets are fetched but never used
In `orchestrator.py` the SERP scraper returns `organic_results[i].snippet` — what Google currently shows as the best answer for each query. This field is collected and then completely discarded before reaching the prompt. The prompt only gets competitor **titles**, not what they actually say.

### Problem D: Competitor content is not analyzed deeply enough
`summarize_competitor_patterns()` in `competitor_analyzer.py` only passes to the prompt:
- Average word count
- Common H2 headings (just the heading text)
- Raw Hebrew word frequency

The actual content text (`content_text`) is fetched and stored but never passed to Gemini. Gemini doesn't know what specific information Google's top-10 pages contain — only their structural metadata.

### Problem E: Prompts force fabricated statistics
`build_blog_prompt()` line 57 explicitly instructs Gemini: "כלול לפחות 3 סטטיסטיקות/מספרים ספציפיים". Gemini will hallucinate these numbers. Fabricated statistics are:
1. A potential spam signal Google's quality systems can detect
2. Directly contradicting the E-E-A-T framework we're trying to signal

### Problem F: Every post has identical structure (AI fingerprint)
All generated posts follow: Intro → Direct Answer block → H2s → FAQ. Google's quality systems can detect this structural pattern across an entire site's content. It's an AI template fingerprint.

### Problem G: gemini-2.5-flash is a speed-optimized model
The config uses `gemini-2.5-flash`. This model prioritizes speed over quality. For content that competes for rankings, the quality ceiling matters.

---

## Part 3: Improvement Plan (Ordered by Impact / Risk)

### STEP 1 — Stop cannibalization: Audit and consolidate duplicate pages
**Status:** [ ] Not started  
**Impact:** Critical — this is actively splitting ranking signals across pages  
**Risk:** Medium — need to handle redirects carefully

**What to do:**
- Identify all pairs/groups of pages that target the same core keyword
- For each group: pick one winner (best-ranking or most-linked), 301 redirect the others to it
- Add a pre-publish check in `orchestrator.py` that blocks new post creation if an existing page (including product/course pages) already ranks or gets impressions for the target keyword
- The current `_is_topic_covered_by_title()` checks blog posts only — expand to also check if any GSC URL already receives impressions for the target keyword

**Specific pages to consolidate (high priority):**
- הנהלת חשבונות: 5 competing pages → consolidate to `/קורס-הנהלת-חשבונות` canonical
- מנהל עבודה בבניין: 3 competing pages → keep strongest, redirect others
- נהג אוטובוס: 3 competing pages → keep strongest
- רכב ציבורי: 2 competing pages

---

### STEP 2 — Pass SERP snippets to the prompt
**Status:** [ ] Not started  
**Impact:** High — tells Gemini what content Google currently rewards for each query  
**Risk:** Low — additive change to prompt only  
**Files:** `orchestrator.py`, `generator/prompts.py`

**What to do:**
In `run_research()` (`orchestrator.py`), extract snippets from SERP results and add them to `topic_data`:
```python
serp_snippets = []
for result in serp.get("organic_results", [])[:5]:
    if result.get("snippet"):
        serp_snippets.append({
            "position": result["position"],
            "title": result["title"],
            "snippet": result["snippet"]
        })
topic_data["serp_snippets"] = serp_snippets
```

In `build_blog_prompt()`, add a new section:
```
=== מה גוגל כרגע מציג כתשובה הטובה ביותר (קטעי SERP) ===
[top 5 snippets with their titles]
זו המסגרת שגוגל כבר מתגמל — התוכן שלך חייב לכסות את אותם נושאים, אבל בצורה עמוקה יותר.
```

---

### STEP 3 — Pass actual competitor content to the prompt
**Status:** [ ] Not started  
**Impact:** High — Gemini currently writes without knowing what competitors actually say  
**Risk:** Low — additive change  
**Files:** `tools/competitor_analyzer.py`, `generator/prompts.py`

**What to do:**
In `summarize_competitor_patterns()`, add `content_previews` field:
```python
content_previews = []
for a in valid[:3]:  # top 3 competitors
    if a.get("content_text"):
        content_previews.append({
            "url": a["url"],
            "title": a["title"],
            "content_preview": a["content_text"][:800]  # first 800 chars
        })
return {
    ...existing fields...,
    "content_previews": content_previews,
}
```

In `build_blog_prompt()`, add a section after competitor analysis:
```
=== תוכן מתחרים מובילים (ראשית הפוסט שלהם) ===
[content previews]
לא להעתיק — להבין מה כיוון הנושא ואז לכסות אותו עמוק יותר.
```

---

### STEP 4 — Fix the fabricated statistics mandate
**Status:** [ ] Not started  
**Impact:** Medium-High — removes likely spam signal  
**Risk:** None — removes harmful instruction  
**Files:** `generator/prompts.py`

**What to do:**
In `build_blog_prompt()` and `build_rewrite_prompt()`, replace the GEO statistics section:

**Current (bad):**
> כלול לפחות 3 סטטיסטיקות/מספרים ספציפיים רלוונטיים לנושא הפוסט — לדוגמה: "X% מהמשתמשים..."

**Replace with:**
> כלול מספרים ספציפיים רק כשאתה בטוח בהם לחלוטין (למשל: משך קורס, מחיר טווח, שנות הכשרה, דרישות רישיון). אל תמציא סטטיסטיקות. פרטים ספציפיים ומאומתים (גם בלי אחוזים) אמינים יותר מנתונים שנראים כממוצאים.

---

### STEP 5 — Fix URL/slug generation to be keyword-clean
**Status:** [ ] Not started  
**Impact:** Medium — long-term signal quality  
**Risk:** Low — affects new posts only  
**Files:** `generator/prompts.py`

**What to do:**
In the SLUG instruction in `build_blog_prompt()`, add explicit length and format constraints:
```
SLUG: [slug באנגלית — מקסימום 4-5 מילים, רק מילת המפתח הראשית, ללא שם האתר, ללא ביטויים שיווקיים]
דוגמה טובה: kurs-menahel-avoda-bvinyan
דוגמה רעה: kurs-menahel-avoda-bvinyan-bmikhlelet-everest-hatzaad-haba-bakaryera-shelkha
```

Add server-side slug validation in `publisher/post_publisher.py` — if slug contains more than 5 hyphen-separated words, truncate to the first 4-5.

---

### STEP 6 — Vary post structure based on search intent
**Status:** [ ] Not started  
**Impact:** Medium — breaks AI fingerprint  
**Risk:** Low — prompt change only  
**Files:** `generator/prompts.py`

**What to do:**
Add intent detection before prompt construction. Three modes:
- **Informational** (what/how/why questions) → Deep guide format, H2s by sub-question
- **Commercial** (pricing, comparison, where to study) → Comparison table format, clear CTAs, minimal FAQ
- **Navigational** (brand + course name) → Concise course description, practical info first

Remove the mandatory "=== תשובה ישירה (לציטוט AI) ===" block from every post. Replace with: only include if the query is clearly a question (contains "מה", "איך", "כמה", "מתי", "האם").

---

### STEP 7 — Image brand consistency with hex colors
**Status:** [ ] Not started  
**Impact:** Medium — brand trust signal, not a ranking factor  
**Risk:** None  
**Files:** `config.everst.yaml`, `generator/prompts.py`

**What to do:**
Add specific hex values to `config.everst.yaml`:
```yaml
image_style:
  brand_hex_primary: "#1B3A6B"    # deep blue
  brand_hex_secondary: "#F5A623"  # warm gold accent
  brand_hex_background: "#FFFFFF" # white
  visual_style: "realistic photography, professional depth-of-field, warm natural lighting"
```

Update `build_image_prompt()` to use hex values:
```
Color grading: dominant #1B3A6B deep blue tones, warm #F5A623 accent highlights, white backgrounds.
Style: realistic photography, professional depth-of-field, 85mm lens equivalent.
Visual consistency: all images from this brand should look like they belong in the same catalogue.
```

---

### STEP 8 — Upgrade generation model
**Status:** [ ] Not started  
**Impact:** Medium — higher quality ceiling, less detectable as AI  
**Risk:** None (cost increase only)  
**Files:** `config.everst.yaml`

**What to do:**
Change `model: "gemini-2.5-flash"` to `model: "gemini-2.5-pro"` in the Everest config for content generation only (keep flash for image concept translation and subtitle generation where quality doesn't matter as much).

Consider running a head-to-head: generate the same post with both models, review quality manually before committing to the upgrade.

---

## Part 4: Measurement Baseline

### Current baseline (as of 2026-04-10, 90d window)
- Total clicks: 522 (90d) / 84 (28d)
- Total impressions: 16,981 (90d) / 1,967 (28d)
- Avg position: 27.0
- Avg CTR: 1.77%
- Pages on page 1 (pos ≤ 10): 3
- Pages on page 2 (pos 11–20): ~5
- Cannibalized queries: 104

### Success metrics (re-measure at 4 weeks and 8 weeks)
| Metric | Target (4 weeks) | Target (8 weeks) |
|---|---|---|
| 28d clicks | > 120 (vs 84 today) | > 200 |
| 28d impressions | > 3,000 (vs 1,967) | > 5,000 |
| Avg position | < 25.0 | < 20.0 |
| Pages pos ≤ 10 | ≥ 5 | ≥ 8 |
| Cannibalized queries | < 60 | < 30 |

---

## Execution Order

| Step | What | When |
|---|---|---|
| 1 | Stop cannibalization — audit + consolidate duplicate pages | First |
| 2 | Pass SERP snippets to prompt | Second |
| 3 | Pass competitor content to prompt | With Step 2 |
| 4 | Remove fabricated statistics mandate | With Step 2 |
| 5 | Fix slug generation to be keyword-clean | After Steps 2-4 test |
| 6 | Vary post structure by intent | After Step 5 |
| 7 | Image brand hex colors | Any time |
| 8 | Upgrade model | After Steps 2-4 live and measurable |

---

## Open Questions Before Starting

1. **Redirects**: For cannibalized pages, does the CMS support 301 redirects? Or do we need to merge content and delete the weaker page?
2. **Which pages to keep**: For each cannibalized group, which page is the "winner" — highest clicks? Lowest position? Oldest?
3. **Blog vs course pages**: Some cannibalization is blog post vs course page. Should blog posts on course-specific topics be deleted entirely and traffic sent to the course page?
