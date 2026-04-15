from datetime import datetime
import json
import os
import pytz
import swisseph as swe

# ---------------- Config ----------------
EPHE_PATH = os.getenv("SWE_EPHE_PATH")
if EPHE_PATH:
    swe.set_ephe_path(EPHE_PATH)

DAYS_PER_YEAR = 365.2425

PLANETS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY, "Venus": swe.VENUS,
    "Mars": swe.MARS, "Jupiter": swe.JUPITER, "Saturn": swe.SATURN,
    "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE, "Pluto": swe.PLUTO,
    "MeanNode": swe.MEAN_NODE, "TrueNode": swe.TRUE_NODE,
}

ZODIAC = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
          "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

SIGN_LORDS = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}

CLASSICAL_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

PLANETARY_ASPECTS = {
    "Sun": {7},
    "Moon": {7},
    "Mars": {4, 7, 8},
    "Mercury": {7},
    "Jupiter": {5, 7, 9},
    "Venus": {7},
    "Saturn": {3, 7, 10},
    "Rahu": {7},
    "Ketu": {7},
}

# Vimshottari
DASHA_ORDER = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]
DASHA_YEARS = {"Ketu":7,"Venus":20,"Sun":6,"Moon":10,"Mars":7,"Rahu":18,"Jupiter":16,"Saturn":19,"Mercury":17}
NAKSHATRA_LORDS = DASHA_ORDER * 3  # 27


# ---------------- Helpers ----------------
def normalize_angle(a):
    v = float(a) % 360.0
    return v if v >= 0 else v + 360.0

def zodiac_sign_from_longitude(lon):
    lon = normalize_angle(lon)
    si = int(lon // 30)
    deg_in = lon - si * 30
    return si, ZODIAC[si], deg_in

def normalize_cusps_array_raw(cusps_raw):
    n = len(cusps_raw)
    if n >= 13:
        return [normalize_angle(float(cusps_raw[i])) for i in range(1,13)]
    elif n == 12:
        return [normalize_angle(float(cusps_raw[i])) for i in range(0,12)]
    else:
        raise RuntimeError(f"Unexpected cusps length {n}")

def build_house_cusps_dict(cusps12):
    return {str(i+1): round(float(cusps12[i]), 6) for i in range(12)}

def safe_calc_speed(jd_ut, pcode):
    try:
        xx_spd, _ = swe.calc_ut(jd_ut, pcode, swe.FLG_SPEED | swe.FLG_SIDEREAL)
        if xx_spd and len(xx_spd) >= 4:
            return float(xx_spd[3])
    except Exception:
        pass
    return None

def jd_to_iso(jd):
    y,m,d,hour = swe.revjul(jd)
    h = int(hour)
    minute = int((hour - h) * 60)
    sec_float = ((hour - h) * 60 - minute) * 60
    s = int(sec_float)
    micro = int(round((sec_float - s) * 1_000_000))
    if micro >= 1_000_000:
        s += 1
        micro -= 1_000_000
    if s >= 60:
        minute += 1
        s -= 60
    if minute >= 60:
        h += 1
        minute -= 60
    try:
        dt = datetime(int(y), int(m), int(d), h, minute, s, micro, tzinfo=pytz.UTC)
        return dt.isoformat()
    except Exception:
        return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"

def get_house_for_longitude(planet_lon, cusps):
    """
    Assign planet to house given its longitude and 12-element cusp list.
    Returns house number 1..12.
    """
    pl = normalize_angle(planet_lon)
    cusp_bounds = [normalize_angle(c) for c in cusps]
    for i in range(12):
        start = cusp_bounds[i]
        end = cusp_bounds[(i + 1) % 12]
        if end <= start:
            end += 360
        pl_mod = pl
        if pl_mod < start:
            pl_mod += 360
        if start <= pl_mod < end:
            return i + 1
    return 12


def current_jd_utc():
    now_utc = datetime.now(tz=pytz.UTC)
    frac_hour = (
        now_utc.hour
        + now_utc.minute / 60.0
        + now_utc.second / 3600.0
        + now_utc.microsecond / 3600.0 / 1e6
    )
    return now_utc, swe.julday(now_utc.year, now_utc.month, now_utc.day, frac_hour)


def house_distance(from_house, to_house):
    return ((int(to_house) - int(from_house)) % 12) + 1


def angle_distance(a, b):
    diff = abs(normalize_angle(a) - normalize_angle(b))
    return min(diff, 360.0 - diff)


def build_house_lords(cusps_used):
    house_lords = {}
    for house_no, cusp_lon in enumerate(cusps_used, start=1):
        sign_index, sign_name, _ = zodiac_sign_from_longitude(cusp_lon)
        house_lords[house_no] = {
            "house": house_no,
            "sign": sign_name,
            "sign_index": sign_index + 1,
            "lord": SIGN_LORDS[sign_name],
        }
    return house_lords


def build_ruled_houses_map(house_lords):
    ruled = {}
    for house_no, data in house_lords.items():
        ruled.setdefault(data["lord"], []).append(house_no)
    return ruled


def has_planetary_aspect(source_planet, source_house, target_house):
    return house_distance(source_house, target_house) in PLANETARY_ASPECTS.get(source_planet, {7})


def planets_are_connected(planet_a, planet_b, planet_map, ruled_houses):
    p1 = planet_map.get(planet_a)
    p2 = planet_map.get(planet_b)
    if not p1 or not p2:
        return []

    connections = []
    if p1["sign_index"] == p2["sign_index"]:
        connections.append("conjunction")
    if has_planetary_aspect(planet_a, p1["house"], p2["house"]) or has_planetary_aspect(planet_b, p2["house"], p1["house"]):
        connections.append("aspect")

    ruled_by_a = set(ruled_houses.get(planet_a, []))
    ruled_by_b = set(ruled_houses.get(planet_b, []))
    if p1["house"] in ruled_by_b and p2["house"] in ruled_by_a:
        connections.append("exchange")

    # Preserve order while removing duplicates.
    return list(dict.fromkeys(connections))


def is_within_arc(start_lon, end_lon, point_lon, epsilon=1e-6):
    start = normalize_angle(start_lon)
    end = normalize_angle(end_lon)
    point = normalize_angle(point_lon)

    if start <= end:
        return start - epsilon <= point <= end + epsilon
    return point >= start - epsilon or point <= end + epsilon


def detect_raj_yoga(house_lords, ruled_houses, planet_map):
    kendra_houses = {4, 7, 10}
    trikona_houses = {5, 9}
    mixed_houses = {3, 6, 8, 11, 12}
    evidence = []
    participants = set()
    primary = []
    conditional = []

    def add_unique(items, entry):
        if entry not in items:
            items.append(entry)

    for planet, houses in ruled_houses.items():
        if kendra_houses.intersection(houses) and trikona_houses.intersection(houses):
            kendra_owned = sorted(kendra_houses.intersection(houses))
            trikona_owned = sorted(trikona_houses.intersection(houses))
            mixed_owned = sorted(mixed_houses.intersection(houses))
            entry = {
                "type": "yogakaraka",
                "planets": [planet],
                "kendra_houses": kendra_owned,
                "trikona_houses": trikona_owned,
            }
            if mixed_owned:
                entry["caveat"] = f"{planet} also rules mixed house(s) {mixed_owned}"
                add_unique(conditional, entry)
                evidence.append(
                    f"{planet} rules kendra house(s) {kendra_owned} and trikona house(s) {trikona_owned}, but also mixed house(s) {mixed_owned}"
                )
            else:
                add_unique(primary, entry)
                evidence.append(
                    f"{planet} rules kendra house(s) {kendra_owned} and trikona house(s) {trikona_owned}"
                )
            participants.add(planet)

    checked = set()
    for kendra_house in sorted(kendra_houses):
        kendra_lord = house_lords[kendra_house]["lord"]
        for trikona_house in sorted(trikona_houses):
            trikona_lord = house_lords[trikona_house]["lord"]
            if kendra_lord == trikona_lord:
                continue
            key = tuple(sorted((kendra_lord, trikona_lord)))
            if key in checked:
                continue
            checked.add(key)
            connections = planets_are_connected(kendra_lord, trikona_lord, planet_map, ruled_houses)
            if connections:
                mixed_lordships = {
                    kendra_lord: sorted(mixed_houses.intersection(ruled_houses.get(kendra_lord, []))),
                    trikona_lord: sorted(mixed_houses.intersection(ruled_houses.get(trikona_lord, []))),
                }
                entry = {
                    "type": "kendra_trikona_connection",
                    "planets": [kendra_lord, trikona_lord],
                    "kendra_house": kendra_house,
                    "trikona_house": trikona_house,
                    "relationship": connections,
                }
                if mixed_lordships[kendra_lord] or mixed_lordships[trikona_lord]:
                    caveat_parts = []
                    if mixed_lordships[kendra_lord]:
                        caveat_parts.append(f"{kendra_lord} also rules {mixed_lordships[kendra_lord]}")
                    if mixed_lordships[trikona_lord]:
                        caveat_parts.append(f"{trikona_lord} also rules {mixed_lordships[trikona_lord]}")
                    entry["caveat"] = "; ".join(caveat_parts)
                    add_unique(conditional, entry)
                    evidence.append(
                        f"{kendra_lord} and {trikona_lord} have {', '.join(connections)} as kendra/trikona lords, with mixed lordship ({entry['caveat']})"
                    )
                else:
                    add_unique(primary, entry)
                    evidence.append(
                        f"{kendra_lord} and {trikona_lord} have {', '.join(connections)} as kendra/trikona lords"
                    )
                participants.update([kendra_lord, trikona_lord])

    return {
        "present": bool(primary),
        "conditional_present": bool(conditional),
        "strength": "strong" if primary else ("conditional" if conditional else "none"),
        "evidence": evidence,
        "participating_planets": sorted(participants),
        "primary_combinations": primary,
        "conditional_combinations": conditional,
    }


def detect_gajakesari_yoga(planet_map):
    moon = planet_map.get("Moon")
    jupiter = planet_map.get("Jupiter")
    if not moon or not jupiter:
        return {"present": False, "evidence": []}

    relationship = house_distance(moon["house"], jupiter["house"])
    if relationship in {1, 4, 7, 10}:
        return {
            "present": True,
            "evidence": [
                f"Jupiter is {relationship} house(s) from Moon, forming a kendra relationship"
            ],
        }
    return {"present": False, "evidence": []}


def detect_budhaditya_yoga(planet_map):
    sun = planet_map.get("Sun")
    mercury = planet_map.get("Mercury")
    if not sun or not mercury:
        return {"present": False, "evidence": []}

    if sun["sign_index"] == mercury["sign_index"]:
        separation = round(angle_distance(sun["longitude_deg"], mercury["longitude_deg"]), 3)
        return {
            "present": True,
            "evidence": [
                f"Sun and Mercury are conjunct in {sun['sign']} with {separation}° separation"
            ],
        }
    return {"present": False, "evidence": []}


def detect_dhana_yoga(house_lords, ruled_houses, planet_map):
    dhana_houses = {2, 5, 9, 11}
    evidence = []
    participants = set()

    for planet, houses in ruled_houses.items():
        owned = sorted(dhana_houses.intersection(houses))
        if len(owned) >= 2:
            evidence.append(f"{planet} rules multiple dhana houses {owned}")
            participants.add(planet)

    for house_no in sorted(dhana_houses):
        lord = house_lords[house_no]["lord"]
        placement = planet_map.get(lord, {}).get("house")
        if placement in dhana_houses and placement != house_no:
            evidence.append(f"{lord}, lord of house {house_no}, is placed in dhana house {placement}")
            participants.add(lord)

    checked = set()
    dhana_lords = sorted({house_lords[house_no]["lord"] for house_no in dhana_houses})
    for i, lord_a in enumerate(dhana_lords):
        for lord_b in dhana_lords[i + 1:]:
            key = tuple(sorted((lord_a, lord_b)))
            if key in checked:
                continue
            checked.add(key)
            connections = planets_are_connected(lord_a, lord_b, planet_map, ruled_houses)
            if connections:
                evidence.append(f"{lord_a} and {lord_b} have {', '.join(connections)} between dhana lords")
                participants.update([lord_a, lord_b])

    return {
        "present": bool(evidence),
        "evidence": evidence,
        "participating_planets": sorted(participants),
    }


def detect_viparita_raja_yoga(house_lords, planet_map):
    dusthana_houses = [6, 8, 12]
    placements = []
    exchanges = []
    participants = set()

    for house_no in dusthana_houses:
        lord = house_lords[house_no]["lord"]
        planet_house = planet_map.get(lord, {}).get("house")
        if planet_house in dusthana_houses and planet_house != house_no:
            placements.append(f"{lord}, lord of house {house_no}, is placed in dusthana house {planet_house}")
            participants.add(lord)

    for idx, house_a in enumerate(dusthana_houses):
        lord_a = house_lords[house_a]["lord"]
        for house_b in dusthana_houses[idx + 1:]:
            lord_b = house_lords[house_b]["lord"]
            if lord_a == lord_b:
                continue
            planet_a_house = planet_map.get(lord_a, {}).get("house")
            planet_b_house = planet_map.get(lord_b, {}).get("house")
            if planet_a_house == house_b and planet_b_house == house_a:
                exchanges.append(f"{lord_a} and {lord_b} exchange dusthana houses {house_a} and {house_b}")
                participants.update([lord_a, lord_b])

    present = bool(exchanges) or len(placements) >= 2
    return {
        "present": present,
        "evidence": placements + exchanges,
        "participating_planets": sorted(participants),
    }


def detect_kaal_sarpa_yoga(planet_map):
    rahu = planet_map.get("TrueNode") or planet_map.get("MeanNode")
    if not rahu:
        return {"present": False, "evidence": []}

    rahu_lon = rahu["longitude_deg"]
    ketu_lon = normalize_angle(rahu_lon + 180.0)
    classical_lons = [planet_map[p]["longitude_deg"] for p in CLASSICAL_PLANETS if p in planet_map]

    within_rahu_to_ketu = all(is_within_arc(rahu_lon, ketu_lon, lon) for lon in classical_lons)
    within_ketu_to_rahu = all(is_within_arc(ketu_lon, rahu_lon, lon) for lon in classical_lons)

    if within_rahu_to_ketu or within_ketu_to_rahu:
        arc_name = "Rahu to Ketu" if within_rahu_to_ketu else "Ketu to Rahu"
        return {
            "present": True,
            "evidence": [
                f"All seven classical planets lie within the {arc_name} arc using {'TrueNode' if 'TrueNode' in planet_map else 'MeanNode'}"
            ],
            "node_basis": "TrueNode" if "TrueNode" in planet_map else "MeanNode",
        }
    return {
        "present": False,
        "evidence": [],
        "node_basis": "TrueNode" if "TrueNode" in planet_map else "MeanNode",
    }


def detect_manglik_dosha(planet_map):
    mars = planet_map.get("Mars")
    if not mars:
        return {"present": False, "evidence": []}

    manglik_houses = {1, 2, 4, 7, 8, 12}
    if mars["house"] in manglik_houses:
        return {
            "present": True,
            "evidence": [f"Mars is placed in house {mars['house']}"],
        }
    return {"present": False, "evidence": []}


def detect_sade_sati(planet_map):
    moon = planet_map.get("Moon")
    if not moon:
        return {"present": False, "evidence": []}

    swe.set_sid_mode(swe.SIDM_LAHIRI)
    evaluated_at, now_jd = current_jd_utc()
    saturn_xx, _ = swe.calc_ut(now_jd, swe.SATURN, swe.FLG_SIDEREAL)
    transit_saturn_lon = normalize_angle(saturn_xx[0])
    transit_saturn_sign_index, transit_saturn_sign, _ = zodiac_sign_from_longitude(transit_saturn_lon)
    relation = house_distance(moon["sign_index"], transit_saturn_sign_index + 1)
    stage_map = {
        12: "Rising phase",
        1: "Peak phase",
        2: "Setting phase",
    }
    present = relation in stage_map
    evidence = []
    if present:
        evidence.append(
            f"Transit Saturn is in {transit_saturn_sign}, which is {relation} house(s) from the natal Moon sign {moon['sign']}"
        )

    return {
        "present": present,
        "stage": stage_map.get(relation),
        "evaluated_at": evaluated_at.isoformat(),
        "transit_saturn": {
            "longitude_deg": round(transit_saturn_lon, 6),
            "sign": transit_saturn_sign,
            "sign_index": transit_saturn_sign_index + 1,
            "house_from_natal_moon": relation,
        },
        "evidence": evidence,
    }


def detect_yogas(cusps_used, planets_out):
    house_lords = build_house_lords(cusps_used)
    ruled_houses = build_ruled_houses_map(house_lords)
    planet_map = {planet["name"]: planet for planet in planets_out if "error" not in planet}

    analysis = {
        "house_lords": {
            str(house_no): {
                "sign": data["sign"],
                "sign_index": data["sign_index"],
                "lord": data["lord"],
            }
            for house_no, data in house_lords.items()
        },
        "raj_yoga": detect_raj_yoga(house_lords, ruled_houses, planet_map),
        "gajakesari_yoga": detect_gajakesari_yoga(planet_map),
        "budhaditya_yoga": detect_budhaditya_yoga(planet_map),
        "dhana_yoga": detect_dhana_yoga(house_lords, ruled_houses, planet_map),
        "viparita_raja_yoga": detect_viparita_raja_yoga(house_lords, planet_map),
        "kaal_sarpa_yoga": detect_kaal_sarpa_yoga(planet_map),
        "manglik_dosha": detect_manglik_dosha(planet_map),
        "sade_sati": detect_sade_sati(planet_map),
    }

    detected = []
    conditional_detected = []
    for key, value in analysis.items():
        if key == "house_lords":
            continue
        if value.get("present"):
            detected.append(key)
        elif value.get("conditional_present"):
            conditional_detected.append(key)
    analysis["detected"] = detected
    analysis["conditional_detected"] = conditional_detected
    return analysis


# ---------------- Vimshottari Dasha ----------------
def find_current_period(periods, target_jd):
    current = None
    for period in periods:
        is_current = period["start_jd"] <= target_jd < period["end_jd"]
        period["is_current"] = bool(is_current)
        if is_current:
            current = period
    return current


def build_subperiods(start_planet, start_jd, total_years):
    periods = []
    idx = DASHA_ORDER.index(start_planet)
    cursor_jd = start_jd
    cycle_end_jd = start_jd + total_years * DAYS_PER_YEAR

    for offset in range(len(DASHA_ORDER)):
        planet = DASHA_ORDER[(idx + offset) % len(DASHA_ORDER)]
        period_years = total_years * (DASHA_YEARS[planet] / 120.0)
        end_jd = cursor_jd + period_years * DAYS_PER_YEAR
        periods.append({"planet": planet, "start_jd": cursor_jd, "end_jd": end_jd})
        cursor_jd = end_jd

    if periods:
        periods[-1]["end_jd"] = cycle_end_jd
    return periods


def serialize_dasha_period(period):
    out = {
        "planet": period["planet"],
        "start": jd_to_iso(period["start_jd"]),
        "end": jd_to_iso(period["end_jd"]),
    }
    if "is_current" in period:
        out["is_current"] = bool(period["is_current"])
    if "antardashas" in period:
        out["antardashas"] = [serialize_dasha_period(antardasha) for antardasha in period["antardashas"]]
    return out


def calc_vimshottari_dasha(jd_ut):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    xx, _ = swe.calc_ut(jd_ut, swe.MOON, swe.FLG_SIDEREAL)
    moon_lon_sid = normalize_angle(xx[0])

    nak_size = 360.0/27.0
    nak_index = int(moon_lon_sid // nak_size)
    first_lord = NAKSHATRA_LORDS[nak_index]

    frac_into = (moon_lon_sid % nak_size) / nak_size
    frac_left = 1.0 - frac_into
    first_maha_years = DASHA_YEARS[first_lord]
    balance_years = frac_left * first_maha_years
    elapsed_years = first_maha_years - balance_years
    first_maha_start_jd = jd_ut - elapsed_years * DAYS_PER_YEAR

    _, today_jd = current_jd_utc()

    mahadasha_timeline = []
    idx = DASHA_ORDER.index(first_lord)
    start_jd = first_maha_start_jd
    for offset in range(len(DASHA_ORDER)):
        p = DASHA_ORDER[(idx + offset) % len(DASHA_ORDER)]
        years = DASHA_YEARS[p]
        end_jd = start_jd + years * DAYS_PER_YEAR
        antardashas = build_subperiods(p, start_jd, years)
        mahadasha_timeline.append({
            "planet": p,
            "start_jd": start_jd,
            "end_jd": end_jd,
            "antardashas": antardashas,
        })
        start_jd = end_jd

    current_maha = find_current_period(mahadasha_timeline, today_jd)
    current_anta = None
    for maha in mahadasha_timeline:
        current_for_maha = find_current_period(maha["antardashas"], today_jd)
        if current_for_maha:
            current_anta = current_for_maha

    current_praty_timeline = []
    current_praty = None
    if current_anta:
        anta_years = (current_anta["end_jd"] - current_anta["start_jd"]) / DAYS_PER_YEAR
        current_praty_timeline = build_subperiods(current_anta["planet"], current_anta["start_jd"], anta_years)
        current_praty = find_current_period(current_praty_timeline, today_jd)

    def ser(d):
        if not d:
            return None
        return {
            "planet": d["planet"],
            "start": jd_to_iso(d["start_jd"]),
            "end": jd_to_iso(d["end_jd"]),
        }

    return {
        "timeline_start": jd_to_iso(first_maha_start_jd),
        "timeline_end": jd_to_iso(mahadasha_timeline[-1]["end_jd"]) if mahadasha_timeline else None,
        "mahadashas": [serialize_dasha_period(mahadasha) for mahadasha in mahadasha_timeline],
        "current": {
            "mahadasha": ser(current_maha),
            "antardasha": ser(current_anta),
            "pratyantardasha": ser(current_praty),
        },
        "current_antardasha_pratyantardashas": [
            {
                "planet": period["planet"],
                "start": jd_to_iso(period["start_jd"]),
                "end": jd_to_iso(period["end_jd"]),
                "is_current": bool(period.get("is_current")),
            }
            for period in current_praty_timeline
        ],
        "birth_mahadasha_balance": {
            "planet": first_lord,
            "remaining_years": round(balance_years, 6),
        },
    }


# --------------- Main generator ---------------
def generate_chart(birth, house_system='WS'):
    required = ["year","month","date","hours","minutes","seconds","timezone","latitude","longitude"]
    for k in required:
        if k not in birth:
            raise ValueError(f"Missing {k}")

    tz = pytz.timezone(birth["timezone"])
    local_dt = datetime(birth["year"], birth["month"], birth["date"],
                        birth["hours"], birth["minutes"], birth["seconds"])
    local_dt = tz.localize(local_dt)
    utc_dt = local_dt.astimezone(pytz.utc)
    frac_hour = utc_dt.hour + utc_dt.minute/60.0 + utc_dt.second/3600.0 + utc_dt.microsecond/3600.0/1e6
    jd_ut_local = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, frac_hour)

    lon = float(birth["longitude"])
    lat = float(birth["latitude"])
    alt = float(birth.get("altitude_m", 0.0))
    try:
        swe.set_topo(lon, lat, alt)
    except Exception:
        pass

    swe.set_sid_mode(swe.SIDM_LAHIRI)

    cusps_raw, ascmc = swe.houses(jd_ut_local, lat, lon, b'P')
    ayan = swe.get_ayanamsa(jd_ut_local)

    asc_trop = normalize_angle(ascmc[0])
    asc_sid = normalize_angle(asc_trop - ayan)
    asc_sign_index, asc_sign_name, asc_deg_in_sign = zodiac_sign_from_longitude(asc_sid)

    cusps12_trop = normalize_cusps_array_raw(cusps_raw)
    cusps12_sid = [normalize_angle(c - ayan) for c in cusps12_trop]

    if str(house_system).upper() in ('WS','WHOLE'):
        asc_sign_start = int(asc_sid // 30) * 30.0
        cusps_used = [normalize_angle(asc_sign_start + i * 30.0) for i in range(12)]
    else:
        cusps_used = cusps12_sid

    planets_out = []
    for pname,pcode in PLANETS.items():
        try:
            xx,_ = swe.calc_ut(jd_ut_local, pcode, swe.FLG_SIDEREAL)
            lon_deg = normalize_angle(xx[0])
            lat_deg = float(xx[1]) if len(xx) > 1 else 0.0
            dist = float(xx[2]) if len(xx) > 2 else None
            speed = safe_calc_speed(jd_ut_local, pcode)
            retro = (speed is not None and speed < 0)
            sign_idx, sign_name, deg_in_sign = zodiac_sign_from_longitude(lon_deg)
            house_no = get_house_for_longitude(lon_deg, cusps_used)
            planets_out.append({
                "name": pname,
                "longitude_deg": round(lon_deg, 6),
                "latitude_deg": round(lat_deg, 6),
                "distance_au": round(dist, 6) if dist is not None else None,
                "sign": sign_name,
                "sign_index": sign_idx + 1,
                "degree_in_sign": round(deg_in_sign, 6),
                "house": house_no,
                "retrograde": bool(retro)
            })
        except Exception as e:
            planets_out.append({"name": pname, "error": str(e)})

    dasha_data = calc_vimshottari_dasha(jd_ut_local)
    yoga_data = detect_yogas(cusps_used, planets_out)
    print("Current dasha", dasha_data["current"])

    out = {
        "input": {
            "local_datetime": local_dt.isoformat(),
            "utc_datetime": utc_dt.isoformat(),
            "timezone": birth["timezone"],
            "latitude": lat, "longitude": lon, "altitude_m": alt,
            "julian_day_ut": jd_ut_local
        },
        "ascendant": {
            "longitude_deg": round(asc_sid, 6),
            "sign": asc_sign_name,
            "sign_index": asc_sign_index + 1,
            "degree_in_sign": round(asc_deg_in_sign, 6)
        },
        "house_cusps_deg": build_house_cusps_dict(cusps_used),
        "planets": planets_out,
        "yoga_analysis": yoga_data,
        "current_dasha": dasha_data["current"],
        "vimshottari_dasha": dasha_data,
        # "notes": f"House system: {'Whole-Sign' if str(house_system).upper().startswith('W') else 'Placidus'} | Sidereal (Lahiri)"
    }
    print("Generated chart data",out)
    return json.dumps(out, indent=2)


# --------------- Demo ----------------
if __name__ == "__main__":
    sample = {
        "year": 2003, "month": 5, "day": 7,
        "hour": 23, "minute": 30, "second": 0,
        "timezone": "Asia/Kolkata",
        "latitude": 25.3708, "longitude":86.4734, "altitude_m": 216
    }
    print(generate_chart(sample, house_system="WS"))
