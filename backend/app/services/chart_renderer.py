import os
import re
import logging
from typing import Dict, List, Any, Optional
from tempfile import TemporaryDirectory
from fastapi import HTTPException
from jyotichart import NorthChart, SouthChart

from app.core.constants import (
    CHART_OPTIONS,
    CHART_STYLES,
    JYOTI_PLANETS,
    PLANET_SHORT_SYMBOLS,
    ZODIAC_SIGNS,
)
from app.services.astrology_service import (
    get_chart_data_for_code,
    build_chart_planet_details,
    derive_ketu_from_chart_data,
    canonical_planet_name,
)

logger = logging.getLogger("nakshatra-backend")


def build_chart_label_suffix(statuses: List[str]) -> str:
    suffix = ""
    if "Retrograde" in statuses:
        suffix += "*"
    if "Exalted" in statuses:
        suffix += "↑"
    elif "Debilitated" in statuses:
        suffix += "↓"
    return suffix


def add_svg_text_attr(open_tag: str, attr_name: str, attr_value: str) -> str:
    if f'{attr_name}="' in open_tag:
        return open_tag
    return open_tag[:-1] + f' {attr_name}="{attr_value}">'


def inject_chart_planet_markers(svg: str, details: List[Dict[str, Any]]) -> str:
    for detail in details:
        base_label = PLANET_SHORT_SYMBOLS.get(detail["name"], detail["name"][:2])
        suffix = build_chart_label_suffix(detail.get("statuses") or [])

        pattern = rf'(<text\b[^>]*class="[^"]*\bplanet\b[^"]*"[^>]*>)(?:\({re.escape(base_label)}\)|{re.escape(base_label)})(</text>)'
        def repl(match: re.Match[str]) -> str:
            open_tag = add_svg_text_attr(match.group(1), "data-planet", detail["name"])
            open_tag = add_svg_text_attr(open_tag, "data-short-name", base_label)
            return f"{open_tag}{base_label}{suffix}{match.group(2)}"

        svg = re.sub(pattern, repl, svg, count=1)

    return svg


def shift_sign_numbers_right(svg: str, shift_px: float = 6.0) -> str:
    def repl(match: re.Match[str]) -> str:
        x_value = float(match.group(1))
        return f'x="{x_value + shift_px:g}"'

    return re.sub(r'x="([0-9]+(?:\.[0-9]+)?)"(?=[^>]*class="sign-num")', repl, svg)


def prepare_planets_for_chart(chart_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    planets = []
    rahu_added = False

    for planet in chart_data.get("planets", []):
        if "error" in planet:
            continue
        canonical_name = canonical_planet_name(planet.get("name"))
        if canonical_name == "Rahu":
            if rahu_added:
                continue
            rahu_added = True
        if canonical_name not in JYOTI_PLANETS or canonical_name == "Ketu":
            continue
        planets.append({
            "name": canonical_name,
            "house": int(planet["house"]),
            "retrograde": bool(planet.get("retrograde", False)),
        })

    ketu = derive_ketu_from_chart_data(chart_data)
    if ketu:
        planets.append({
            "name": "Ketu",
            "house": int(ketu["house"]),
            "retrograde": True,
        })

    return planets


def style_chart_object(chart: Any, style: str) -> None:
    house_fills = ["#0f172a"] * 12
    if style == "north":
        chart.updatechartcfg(
            aspect=False,
            clr_background="#020617",
            clr_outbox="#334155",
            clr_line="#64748b",
            clr_sign="#cbd5e1",
            clr_houses=house_fills,
        )
    else:
        chart.updatechartcfg(
            aspect=False,
            clr_background="#020617",
            clr_outbox="#334155",
            clr_inbox="#334155",
            clr_line="#64748b",
            clr_Asc="#cbd5e1",
            clr_houses=house_fills,
        )


def normalize_sign_for_jyotichart(sign_name: Optional[str]) -> Optional[str]:
    if not sign_name:
        return sign_name
    # jyotichart expects a misspelled Sagittarius string internally.
    if sign_name == "Sagittarius":
        return "Saggitarius"
    return sign_name


def render_chart_svg(
    kundli: Dict[str, Any],
    chart_code: str,
    style: str,
    person_name: Optional[str] = None,
) -> str:
    chart_data = get_chart_data_for_code(kundli, chart_code)
    ascendant = chart_data.get("ascendant") or {}
    asc_sign = ascendant.get("sign")
    if not asc_sign:
        raise HTTPException(status_code=500, detail=f"{chart_code} chart is missing ascendant data")

    chart_title = CHART_OPTIONS.get(chart_code, {}).get("label", chart_code)
    safe_name = (person_name or "native").replace(" ", "_")

    if style == "north":
        chart_obj = NorthChart(chart_title, safe_name)
    elif style == "south":
        chart_obj = SouthChart(chart_title, safe_name)
    else:
        raise HTTPException(status_code=400, detail="Unsupported chart style")

    chart_obj.set_ascendantsign(normalize_sign_for_jyotichart(asc_sign))
    style_chart_object(chart_obj, style)
    chart_details = build_chart_planet_details(kundli, chart_code)

    for planet in prepare_planets_for_chart(chart_data):
        chart_obj.add_planet(
            JYOTI_PLANETS[planet["name"]],
            PLANET_SHORT_SYMBOLS[planet["name"]],
            planet["house"],
            retrograde=planet["retrograde"],
            colour="#f8fafc",
        )

    with TemporaryDirectory() as temp_dir:
        file_name = f"{chart_code.lower()}_{style}"
        chart_obj.draw(temp_dir, file_name)
        svg_path = os.path.join(temp_dir, f"{file_name}.svg")
        with open(svg_path, "r", encoding="utf-16") as svg_file:
            svg = svg_file.read()

    svg = svg.replace(
        ".planet { font-size: 20px; font-weight: bold; font-family: sans-serif; }",
        ".planet { font-size: 16px; font-weight: bold; font-family: sans-serif; cursor: pointer; }"
        "\n    .planet-hover { transition: transform 140ms ease, fill 140ms ease; transform-box: fill-box; transform-origin: center; }"
        "\n    .planet-hover:hover { transform: scale(1.18); fill: #ffffff; }",
    )
    svg = svg.replace('class="planet"', 'class="planet planet-hover"')
    svg = svg.replace(".sign-num { font-size: 22px;", ".sign-num { font-size: 17px;")
    svg = svg.replace(' text-decoration="underline"', "")
    svg = re.sub(r'(<text[^>]*class="sign-num"[^>]*>)(0)([1-9])(<\/text>)', r"\1\3\4", svg)
    svg = shift_sign_numbers_right(svg)
    svg = inject_chart_planet_markers(svg, chart_details)

    return svg
