# SEO Audit Report — sciencesgates.com

**Date:** 2026-08-10
**Scope:** Full-site audit — 5 parallel specialist analyses (Technical, Content/E-E-A-T, Schema, Sitemap, Performance)
**Site type:** Arabic study-abroad consultancy (study in Malaysia) — education agency, RTL / `ar`
**Method:** Claude SEO sub-agent pipeline (skills: seo-technical, seo-content, seo-schema, seo-sitemap, seo-performance)

---

## Executive Summary

| Scorecard | Score | Verdict |
|---|---|---|
| Technical SEO | **79/100** | Solid foundation |
| Content & E-E-A-T | **59/100 (Grade C)** | Good base, trust gaps |
| Schema.org | **Grade B** | Valid base, missing coverage |
| XML Sitemap | **Valid ✅** | 184/184 HTTP 200 |
| Performance (lab) | **88/100** | LCP needs improvement |

The site has a healthy technical foundation (server-rendered Django/Rails app behind Cloudflare, valid sitemap, clean canonical structure, strong security headers, no critical indexability failures). The main gaps are trust-related (broken legal pages, unverifiable authority claims), a slow LCP, missing schema coverage, and content-QA artifacts.

---

## Top Priorities (cross-cutting)

| # | Priority | Impact | Source report |
|---|---|---|---|
| P0 | **Restore `/privacy` and `/terms`** (both 404, linked in every footer) | Trust / YMYL | content |
| P1 | **LCP 3.6s** — add `fetchpriority="high"` to the hero LCP image + defer ~20 partner images | Core Web Vitals | performance |
| P1 | **Schema**: add `BreadcrumbList` + `Article`/`BlogPosting` + `telephone`/`email` in Organization | Rich results | schema |
| P1 | **Sitemap**: add 7 missing `/majors/category/` pages; normalize `lastmod`; drop `<priority>/<changefreq>` | Coverage | sitemap |
| P1 | **robots.txt AI crawlers**: token `ClaudeBot` (not legacy `anthropic-ai`); decide on PerplexityBot / Bytespider / Google-Extended | AI visibility | technical |
| P2 | **Content QA**: remove leftover `[wptb]` shortcode, complete truncated FAQ answer, dedupe repeated question | Quality | content |
| P2 | **Company identity**: street address, SSM registration, verify "official agent" claims, soften "100% guaranteed" phrasing | Trust | content |
| P2 | **Long URLs**: 174/184 exceed 100 chars (max 238) — shorten Arabic slugs, drop year tokens | URL structure | technical |
| P2 | **Add Content-Security-Policy** + Permissions-Policy; remove `X-Powered-By` | Security | technical |
| P2 | **Reserve dimensions** on images missing width/height (24/49) | CLS | technical |
| P3 | **IndexNow** not implemented — add key + ping on publish (Bing/Yandex/Naver) | Freshness | technical |

---

## 1. Technical SEO — 79/100

| Category | Status | Score |
|---|---|---|
| Crawlability | ✅ Pass | 92 |
| Indexability | ✅ Pass | 85 |
| Security | ✅ Pass | 88 |
| URL Structure | ⚠️ Warn | 68 |
| Mobile | ⚠️ Warn | 78 |
| Core Web Vitals | ⚠️ Warn | 74 |
| Structured Data | ✅ Pass | 92 |
| JS Rendering | ✅ Pass | 90 |
| IndexNow | ❌ Fail | 40 |

**Passes:** robots.txt valid & declares sitemap; sitemap 184 URLs all 200; canonicals self-referencing; hreflang `ar` correct; HTTPS enforced (301s clean); HSTS + X-Frame-Options DENY + nosniff + Referrer-Policy + COOP present; no mixed content; fully server-rendered (no SPA issues); 4 valid JSON-LD blocks.

**Failures / warnings:**
- robots.txt uses legacy `anthropic-ai` token — current token is `ClaudeBot`; PerplexityBot, Bytespider, Google-Extended unblocked.
- `Disallow: /*&` too aggressive (blocks any URL containing `&`).
- `Crawl-delay` deprecated by Google/Bing — remove.
- Missing CSP and Permissions-Policy; `X-Powered-By: Phusion Passenger(R) 6.1.2` leaks stack version.
- 24/49 `<img>` tags lack width/height (CLS risk); mobile offcanvas nav is JS-cloned (no `<noscript>` fallback).
- 404 page lacks `<meta name="robots" content="noindex">`.
- Organization `logo` schema points at a 600×600 JPG; prefer transparent PNG/SVG.
- `og:locale` is `ar_SA` while content is pan-Arabic.

---

## 2. Content & E-E-A-T — 59/100 (Grade C)

| Factor | Score |
|---|---|
| Experience | 14/20 |
| Expertise | 17/25 |
| Authoritativeness | 12/25 |
| Trustworthiness | 16/30 |

**Strengths:** Named, credentialed leadership (Dr. Mohammad Kayali, PhD Computer Science, UKM); 10+ years / 3,000+ students claims; process walkthrough; real domain knowledge (EMGS, MOI letters, eVAL/eVisa); rich home (~1,400 words) and about pages; working contact form with privacy notice.

**Critical findings:**
1. **P0 — Broken legal pages:** `/privacy` and `/terms` both return 404 while linked in every footer. Highest-damage trust issue for a company handling student PII.
2. **P1 — Scaled-content QA artifacts:** leftover `[wptb id=14730]` shortcode visible, truncated FAQ answer leaking a `##` heading, duplicate "can students work?" question — textbook low-quality-pattern per Sept 2025 QRG.
3. **P1 — Unverifiable business identity:** no street address, no SSM registration, "official agent" and "100% guaranteed acceptance" claims unproven (absolute-guarantee phrasing is a trust red flag).
4. **P2 — Author entity incomplete:** no author bio page, no Person schema, bylines missing on some articles.
5. **P2 — No external authority:** no outbound citations to EMGS, MQA, or university pages.
6. **P2 — Unverifiable testimonials:** Google-review quotes without links/dates.

**AI citation readiness: 62/100** — FAQPage schema + answer-first formatting + data tables good; broken answer, duplicate questions, and no Person/Article schema hold it back. Readability: no concerns (Flesch is N/A for Arabic; clear H1→H2→H3, good scannability).

---

## 3. Schema.org — Grade B

**Detection:** 4 JSON-LD blocks (server-rendered in `<head>`) — WebSite, Organization, WebPage, FAQPage. No Microdata, no RDFa. No deprecated types.

| Type | Status | Issues |
|---|---|---|
| WebSite | ✅ Pass | `SearchAction` absent (fine — no search URL) |
| Organization | ⚠️ Minor | `contactPoint` missing `telephone`/`email`; `sameAs` includes a `wa.me` link (not a social profile) |
| WebPage | ⚠️ Minor | No `isPartOf`/`mainEntity`/`breadcrumb`; `publisher.name` ("Science Gates") mismatches Organization name (Arabic) |
| FAQPage | ℹ️ Info | Structurally perfect, but FAQ rich results retired 2026-05-07 — no Google SERP benefit |

**Missing high-value types:** `BreadcrumbList` (High), `Article`/`BlogPosting` (High), `ItemList` for section cards (Medium), `Organization` enrichment — `telephone`, `email`, `postalAddress` (Kuala Lumpur, MY), `areaServed` (Medium), `Service` + `Offer` (Low), `VideoObject` (Low).

**Recommended additions (JSON-LD):**
```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "الرئيسية", "item": "https://sciencesgates.com/" }
  ]
}
```
```json
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "name": "أحدث المقالات",
  "itemListOrder": "https://schema.org/ItemListOrderDescending",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "item": {
        "@type": "BlogPosting",
        "headline": "الدراسة في ماليزيا",
        "url": "https://sciencesgates.com/articles/study-in-malaysia/",
        "datePublished": "2026-01-05",
        "author": { "@type": "Person", "name": "Dr Mohammad Kayali" },
        "image": "https://sciencesgates.com/media/cache/thumbnails/media_library/editor/20260717_013024_study_in_malaysia_360x240.webp",
        "publisher": { "@type": "Organization", "name": "شركة بوابات العلوم للدراسة في ماليزيا" }
      } } ]
}
```
Also: add `telephone` + `email` + `address` to the existing Organization block; remove `wa.me` from `sameAs`; unify `WebPage.publisher.name` with the Organization name.

---

## 4. XML Sitemap — VALID ✅

- **URL:** `https://sciencesgates.com/sitemap.xml` — declared in robots.txt AND validated live (HTTP 200, well-formed `<urlset>`).
- **Total:** 184 unique URLs, 56 KB (well under limits). 100% HTTPS. **184/184 return HTTP 200** at the exact sitemap URL — zero 404s, zero redirects.
- **No sitemap URL is blocked** by robots.txt rules; no noindexed URLs found; canonicals match.

**Issues:**
1. **Medium — Coverage gap:** 7 indexable `/majors/category/` archive pages are linked on-site but absent from the sitemap.
2. **Low — `lastmod`:** 7 entries missing (root, `/about-us/`, `/visa-tracking/`, 4 hubs); remaining `lastmod` values are batch-stamped (10 distinct values across 184) — not verifiable, so Google may ignore them.
3. **Info — Deprecated tags:** all entries carry `<priority>` and `<changefreq>` — ignored by Google, removable.
4. **Info:** Section pagination via `?page=` is robots-disallowed; sitemap compensates — keep it complete.

**Verdict:** Do NOT regenerate. Targeted patches only: add the 7 category pages, normalize/remove `lastmod`, strip deprecated tags, resubmit in GSC.

---

## 5. Performance / Core Web Vitals — 88/100 (lab)

> Note: PageSpeed Insights + CrUX field data unavailable (API quota exhausted / no key). Lab data via local Lighthouse 12.8.2 (mobile, throttled). Treat as diagnostic; field CWV unverified (site may be low-traffic / CrUX-ineligible).

**Lab scores:** Performance 90 | Accessibility 96 (color-contrast) | Best Practices 96 (image-size-responsive) | SEO 100

| Metric | Value (lab) | Status |
|---|---|---|
| LCP | 3.60 s | ⚠️ Needs Improvement (2.5–4.0s band) |
| INP | TBT 30 ms (proxy) | ✅ Likely Good (<200ms) |
| CLS | 0.000 | ✅ Good |
| FCP / TTFB | 1.3 s / 40 ms | ✅ Excellent |

**LCP root cause:** LCP element is a decorative hero shape (`shape-2-...webp`, displayed 280×186) — lacks `fetchpriority="high"` and is oversized for its display box. Subparts: TTFB 672ms · Load Delay 723ms · Load Time 1,928ms (54%) · Render Delay 273ms.

**Opportunities (est. savings):**
1. `fetchpriority="high"` (+ optional preload) on LCP image → cuts ~700ms, gets LCP under 2.5s
2. Defer ~20 offscreen partner/logo images (347 KiB) → ~300ms
3. Responsive `srcset`/`sizes` for LCP shape + logo → ~14 KiB
4. Purge unused CSS (28 KiB of 35 KiB bundle) → ~150ms
5. Defer GTM/gtag.js (166 KiB) → protects INP + TTI

---

## Methodology & Caveats

- Recommendations follow Google's primary-source guidance (Search Essentials, Quality Rater Guidelines Sept 2025, AI Optimization Guide).
- Every recommendation here is a heuristic scored finding, not a Google-internal signal.
- Field-data CWV (CrUX) and live PSI scores should be confirmed once API quota resets or a CrUX API key is configured.
- A full duplicate-content pass over the programmatic page families (37 universities / 20 institutes / 60 majors) is advised before scaling further.
