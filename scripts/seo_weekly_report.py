#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote
from xml.etree import ElementTree

import requests
from dotenv import load_dotenv
from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account


SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
SEARCH_ANALYTICS_API = "https://www.googleapis.com/webmasters/v3/sites/{site_url}/searchAnalytics/query"
URL_INSPECTION_API = "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect"


@dataclass
class DateRange:
    label: str
    start_date: str
    end_date: str


def load_environment() -> None:
    load_dotenv(".env.seo")
    load_dotenv()
    load_dotenv("frontend/.env.local")


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_brand_terms() -> list[str]:
    raw = os.getenv("SEO_BRAND_TERMS", "nakshatra ai,nakshatra-ai,nakshatra")
    return [term.strip().lower() for term in raw.split(",") if term.strip()]


def get_long_tail_terms() -> list[str]:
    raw = os.getenv(
        "SEO_LONG_TAIL_TERMS",
        "kundli,vedic astrology,navamsa,dasha,mangal dosh,panchang,nakshatra,compatibility",
    )
    return [term.strip().lower() for term in raw.split(",") if term.strip()]


def build_session() -> AuthorizedSession:
    credentials = service_account.Credentials.from_service_account_file(
        get_required_env("GOOGLE_SERVICE_ACCOUNT_FILE"),
        scopes=SCOPES,
    )
    return AuthorizedSession(credentials)


def get_weekly_ranges() -> tuple[DateRange, DateRange]:
    today = date.today()
    current_end = today - timedelta(days=1)
    current_start = current_end - timedelta(days=6)
    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=6)
    return (
        DateRange("current", current_start.isoformat(), current_end.isoformat()),
        DateRange("previous", previous_start.isoformat(), previous_end.isoformat()),
    )


def post_json(session: AuthorizedSession, url: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = session.post(url, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


def fetch_search_rows(
    session: AuthorizedSession,
    property_url: str,
    date_range: DateRange,
    dimensions: list[str],
    row_limit: int = 25000,
    filters: list[dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    site_url = quote(property_url, safe="")
    payload: dict[str, Any] = {
        "startDate": date_range.start_date,
        "endDate": date_range.end_date,
        "dimensions": dimensions,
        "rowLimit": row_limit,
    }
    if filters:
        payload["dimensionFilterGroups"] = [{"groupType": "and", "filters": filters}]
    data = post_json(session, SEARCH_ANALYTICS_API.format(site_url=site_url), payload)
    return data.get("rows", [])


def sum_metrics(rows: list[dict[str, Any]]) -> dict[str, float]:
    return {
        "clicks": round(sum(float(row.get("clicks", 0)) for row in rows), 2),
        "impressions": round(sum(float(row.get("impressions", 0)) for row in rows), 2),
        "ctr": round(
            (
                sum(float(row.get("clicks", 0)) for row in rows)
                / sum(float(row.get("impressions", 0)) for row in rows)
            )
            * 100,
            2,
        )
        if sum(float(row.get("impressions", 0)) for row in rows)
        else 0.0,
        "position": round(
            sum(float(row.get("position", 0)) * float(row.get("impressions", 0)) for row in rows)
            / sum(float(row.get("impressions", 0)) for row in rows),
            2,
        )
        if sum(float(row.get("impressions", 0)) for row in rows)
        else 0.0,
    }


def query_value(row: dict[str, Any]) -> str:
    keys = row.get("keys") or []
    return str(keys[0] if keys else "").strip()


def split_brand_rows(rows: list[dict[str, Any]], brand_terms: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    branded: list[dict[str, Any]] = []
    non_branded: list[dict[str, Any]] = []

    for row in rows:
        query = query_value(row).lower()
        if any(term in query for term in brand_terms):
            branded.append(row)
        else:
            non_branded.append(row)

    return branded, non_branded


def select_long_tail_rows(rows: list[dict[str, Any]], target_terms: list[str]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for row in rows:
        query = query_value(row).lower()
        if len(query.split()) < 4:
            continue
        if any(term in query for term in target_terms):
            matches.append(row)
    matches.sort(key=lambda row: (float(row.get("impressions", 0)), float(row.get("clicks", 0))), reverse=True)
    return matches[:15]


def fetch_sitemap_urls(sitemap_url: str) -> list[str]:
    response = requests.get(sitemap_url, timeout=30)
    response.raise_for_status()
    root = ElementTree.fromstring(response.text)
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [node.text.strip() for node in root.findall("sm:url/sm:loc", namespace) if node.text]


def inspect_urls(
    session: AuthorizedSession,
    property_url: str,
    urls: list[str],
) -> dict[str, Any]:
    max_urls = int(os.getenv("SEO_MAX_INSPECTION_URLS", "100"))
    selected_urls = urls[:max_urls]
    coverage_counter: Counter[str] = Counter()
    indexed_count = 0
    inspected_rows: list[dict[str, Any]] = []

    for url in selected_urls:
        payload = {
            "inspectionUrl": url,
            "siteUrl": property_url,
            "languageCode": "en-US",
        }
        data = post_json(session, URL_INSPECTION_API, payload)
        result = (((data.get("inspectionResult") or {}).get("indexStatusResult")) or {})
        coverage_state = str(result.get("coverageState") or "Unknown")
        coverage_counter[coverage_state] += 1
        is_indexed = "indexed" in coverage_state.lower() and "not indexed" not in coverage_state.lower()
        if is_indexed:
            indexed_count += 1
        inspected_rows.append(
            {
                "url": url,
                "coverage_state": coverage_state,
                "verdict": result.get("verdict"),
                "indexing_state": result.get("indexingState"),
                "last_crawl_time": result.get("lastCrawlTime"),
                "google_canonical": result.get("googleCanonical"),
                "user_canonical": result.get("userCanonical"),
            }
        )

    return {
        "inspected_url_count": len(selected_urls),
        "indexed_url_estimate": indexed_count,
        "coverage_breakdown": dict(coverage_counter),
        "urls": inspected_rows,
        "note": "Indexed page count is an estimate derived from URL Inspection coverage states for URLs found in sitemap.xml.",
    }


def normalize_page_rows(rows: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows[:limit]:
        output.append(
            {
                "page": query_value(row),
                "clicks": round(float(row.get("clicks", 0)), 2),
                "impressions": round(float(row.get("impressions", 0)), 2),
                "ctr": round(float(row.get("ctr", 0)) * 100, 2),
                "position": round(float(row.get("position", 0)), 2),
            }
        )
    return output


def normalize_query_rows(rows: list[dict[str, Any]], limit: int = 15) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows[:limit]:
        output.append(
            {
                "query": query_value(row),
                "clicks": round(float(row.get("clicks", 0)), 2),
                "impressions": round(float(row.get("impressions", 0)), 2),
                "ctr": round(float(row.get("ctr", 0)) * 100, 2),
                "position": round(float(row.get("position", 0)), 2),
            }
        )
    return output


def format_delta(current: float, previous: float) -> str:
    if previous == 0:
        return "new"
    delta = ((current - previous) / previous) * 100
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta:.1f}%"


def write_report(report: dict[str, Any]) -> Path:
    reports_dir = Path("reports/seo")
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d")
    report_path = reports_dir / f"weekly-{stamp}.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    summary_path = reports_dir / f"weekly-{stamp}.md"
    summary_lines = [
        "# SEO Weekly Report",
        "",
        f"- Site: `{report['site_url']}`",
        f"- Current window: `{report['date_ranges']['current']['start_date']}` to `{report['date_ranges']['current']['end_date']}`",
        f"- Previous window: `{report['date_ranges']['previous']['start_date']}` to `{report['date_ranges']['previous']['end_date']}`",
        "",
        "## Search Summary",
        f"- Branded clicks: `{report['branded']['current']['clicks']}` ({report['branded']['delta']['clicks']})",
        f"- Non-branded clicks: `{report['non_branded']['current']['clicks']}` ({report['non_branded']['delta']['clicks']})",
        f"- Homepage CTR: `{report['homepage_ctr']['current']['ctr']}%` ({report['homepage_ctr']['delta']['ctr']})",
        f"- Estimated indexed sitemap URLs: `{report['indexation']['indexed_url_estimate']}` / `{report['indexation']['inspected_url_count']}`",
        "",
        "## Top Landing Pages",
    ]
    for row in report["top_landing_pages"]:
        summary_lines.append(
            f"- `{row['page']}` — {row['clicks']} clicks, {row['impressions']} impressions, {row['ctr']}% CTR, avg position {row['position']}"
        )
    summary_lines.append("")
    summary_lines.append("## Long-Tail Vedic Queries")
    for row in report["long_tail_queries"]:
        summary_lines.append(
            f"- `{row['query']}` — {row['impressions']} impressions, {row['clicks']} clicks, {row['ctr']}% CTR"
        )
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
    return report_path


def main() -> None:
    load_environment()
    session = build_session()
    site_url = (os.getenv("SEO_SITE_URL") or os.getenv("NEXT_PUBLIC_SITE_URL") or "https://nakshatra-ai.tech").rstrip("/")
    property_url = os.getenv("GOOGLE_SEARCH_CONSOLE_PROPERTY", f"{site_url}/")
    homepage_url = f"{site_url}/"
    sitemap_url = f"{site_url}/sitemap.xml"
    brand_terms = get_brand_terms()
    long_tail_terms = get_long_tail_terms()
    current_range, previous_range = get_weekly_ranges()

    current_query_rows = fetch_search_rows(session, property_url, current_range, ["query"])
    previous_query_rows = fetch_search_rows(session, property_url, previous_range, ["query"])
    branded_current_rows, non_branded_current_rows = split_brand_rows(current_query_rows, brand_terms)
    branded_previous_rows, non_branded_previous_rows = split_brand_rows(previous_query_rows, brand_terms)

    homepage_current_rows = fetch_search_rows(
        session,
        property_url,
        current_range,
        ["page"],
        filters=[{"dimension": "page", "operator": "equals", "expression": homepage_url}],
    )
    homepage_previous_rows = fetch_search_rows(
        session,
        property_url,
        previous_range,
        ["page"],
        filters=[{"dimension": "page", "operator": "equals", "expression": homepage_url}],
    )

    top_pages_rows = fetch_search_rows(session, property_url, current_range, ["page"], row_limit=20)
    sitemap_urls = fetch_sitemap_urls(sitemap_url)
    indexation_summary = inspect_urls(session, property_url, sitemap_urls)

    branded_current = sum_metrics(branded_current_rows)
    branded_previous = sum_metrics(branded_previous_rows)
    non_branded_current = sum_metrics(non_branded_current_rows)
    non_branded_previous = sum_metrics(non_branded_previous_rows)
    homepage_current = sum_metrics(homepage_current_rows)
    homepage_previous = sum_metrics(homepage_previous_rows)

    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "site_url": site_url,
        "property_url": property_url,
        "date_ranges": {
            "current": current_range.__dict__,
            "previous": previous_range.__dict__,
        },
        "branded": {
            "current": branded_current,
            "previous": branded_previous,
            "delta": {
                "clicks": format_delta(branded_current["clicks"], branded_previous["clicks"]),
                "impressions": format_delta(branded_current["impressions"], branded_previous["impressions"]),
                "ctr": format_delta(branded_current["ctr"], branded_previous["ctr"]),
            },
            "top_queries": normalize_query_rows(branded_current_rows, limit=10),
        },
        "non_branded": {
            "current": non_branded_current,
            "previous": non_branded_previous,
            "delta": {
                "clicks": format_delta(non_branded_current["clicks"], non_branded_previous["clicks"]),
                "impressions": format_delta(non_branded_current["impressions"], non_branded_previous["impressions"]),
                "ctr": format_delta(non_branded_current["ctr"], non_branded_previous["ctr"]),
            },
            "top_queries": normalize_query_rows(non_branded_current_rows, limit=15),
        },
        "homepage_ctr": {
            "current": homepage_current,
            "previous": homepage_previous,
            "delta": {
                "clicks": format_delta(homepage_current["clicks"], homepage_previous["clicks"]),
                "impressions": format_delta(homepage_current["impressions"], homepage_previous["impressions"]),
                "ctr": format_delta(homepage_current["ctr"], homepage_previous["ctr"]),
            },
        },
        "top_landing_pages": normalize_page_rows(top_pages_rows, limit=10),
        "long_tail_queries": normalize_query_rows(select_long_tail_rows(current_query_rows, long_tail_terms), limit=15),
        "indexation": indexation_summary,
    }

    report_path = write_report(report)
    print(f"SEO weekly report written to {report_path}")


if __name__ == "__main__":
    main()
