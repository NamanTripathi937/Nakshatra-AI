# SEO Measurement Pipeline

This project includes a weekly Search Console reporting script at [`scripts/seo_weekly_report.py`](../scripts/seo_weekly_report.py).

## What it tracks

- branded queries
- non-branded queries
- homepage CTR
- top landing pages
- impressions for long-tail Vedic queries
- an indexed-page estimate based on URL Inspection for URLs found in `sitemap.xml`

## Setup

1. Create a Google service account in Google Cloud.
2. Enable the Search Console API for that Google Cloud project.
3. Add the service account email as an owner or delegated user on your Search Console property.
4. Copy [`.env.seo.example`](../.env.seo.example) to `.env.seo` and fill in the values.
5. Install the reporting dependencies from [`requirements-seo.txt`](../requirements-seo.txt).

## Run the report

```bash
cd /Users/namtripa/Documents/Projects/Nakshatra-AI
python3 -m venv .venv-seo
source .venv-seo/bin/activate
pip install -r requirements-seo.txt
python scripts/seo_weekly_report.py
```

The script writes both JSON and Markdown reports to `reports/seo/`.

## Suggested weekly review

1. Check branded clicks and branded CTR first. If this is weak, the title, snippet, and trust signals for your own brand still need work.
2. Check non-branded impressions and clicks next. This shows whether the new keyword pages and guides are gaining discovery.
3. Review the homepage CTR separately. If impressions rise but CTR stays weak, tighten the title and meta description again.
4. Review the top landing pages list. Double down on pages already getting impressions instead of spreading effort too thin.
5. Scan the long-tail query list for wins. These are often the easiest keywords to turn into top-3 rankings first.
6. Review the indexation estimate from URL Inspection and compare it with new pages added to the sitemap.

## Search Console and Bing verification

- Google Search Console support is already in the site metadata.
- Bing Webmaster verification is supported through `NEXT_PUBLIC_BING_SITE_VERIFICATION` in `frontend/.env.local`.
- External account connection still has to be completed in your own Google and Bing webmaster dashboards.
