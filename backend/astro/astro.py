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
VEDIC_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

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

EXALTATION_SIGNS = {
    "Sun": {"sign": "Aries", "degree": 10.0},
    "Moon": {"sign": "Taurus", "degree": 3.0},
    "Mars": {"sign": "Capricorn", "degree": 28.0},
    "Mercury": {"sign": "Virgo", "degree": 15.0},
    "Jupiter": {"sign": "Cancer", "degree": 5.0},
    "Venus": {"sign": "Pisces", "degree": 27.0},
    "Saturn": {"sign": "Libra", "degree": 20.0},
}

DEBILITATION_SIGNS = {
    "Sun": {"sign": "Libra", "degree": 10.0},
    "Moon": {"sign": "Scorpio", "degree": 3.0},
    "Mars": {"sign": "Cancer", "degree": 28.0},
    "Mercury": {"sign": "Pisces", "degree": 15.0},
    "Jupiter": {"sign": "Capricorn", "degree": 5.0},
    "Venus": {"sign": "Virgo", "degree": 27.0},
    "Saturn": {"sign": "Aries", "degree": 20.0},
}

OWN_SIGNS = {
    "Sun": {"Leo"},
    "Moon": {"Cancer"},
    "Mars": {"Aries", "Scorpio"},
    "Mercury": {"Gemini", "Virgo"},
    "Jupiter": {"Sagittarius", "Pisces"},
    "Venus": {"Taurus", "Libra"},
    "Saturn": {"Capricorn", "Aquarius"},
}

MOOLATRIKONA_RANGES = {
    "Sun": {"sign": "Leo", "start_deg": 0.0, "end_deg": 20.0},
    "Moon": {"sign": "Taurus", "start_deg": 4.0, "end_deg": 30.0},
    "Mars": {"sign": "Aries", "start_deg": 0.0, "end_deg": 12.0},
    "Mercury": {"sign": "Virgo", "start_deg": 16.0, "end_deg": 20.0},
    "Jupiter": {"sign": "Sagittarius", "start_deg": 0.0, "end_deg": 10.0},
    "Venus": {"sign": "Libra", "start_deg": 0.0, "end_deg": 15.0},
    "Saturn": {"sign": "Aquarius", "start_deg": 0.0, "end_deg": 20.0},
}

COMBUSTION_THRESHOLDS = {
    "Moon": 12.0,
    "Mars": 17.0,
    "Mercury": {"direct": 14.0, "retrograde": 12.0},
    "Jupiter": 11.0,
    "Venus": {"direct": 10.0, "retrograde": 8.0},
    "Saturn": 15.0,
}

FUNCTIONAL_HOUSE_SCORES = {
    1: 2,
    2: -1,
    3: -2,
    4: 1,
    5: 2,
    6: -2,
    7: -1,
    8: -2,
    9: 2,
    10: 1,
    11: -2,
    12: -1,
}

# Vimshottari
DASHA_ORDER = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]
DASHA_YEARS = {"Ketu":7,"Venus":20,"Sun":6,"Moon":10,"Mars":7,"Rahu":18,"Jupiter":16,"Saturn":19,"Mercury":17}
NAKSHATRA_LORDS = DASHA_ORDER * 3  # 27
NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]
NAKSHATRA_SIZE = 360.0 / 27.0
PADA_SIZE = NAKSHATRA_SIZE / 4.0
DIVISIONAL_CHART_META = {
    "D9": {
        "division": 9,
        "name": "Navamsha",
        "purpose": "Marriage, spouse character, dharma, and inner strength of the chart",
    },
    "D10": {
        "division": 10,
        "name": "Dashamsha",
        "purpose": "Career, profession, status, and public work",
    },
}


# ---------------- Helpers ----------------
def normalize_angle(a):
    v = float(a) % 360.0
    return v if v >= 0 else v + 360.0

def zodiac_sign_from_longitude(lon):
    lon = normalize_angle(lon)
    si = int(lon // 30)
    deg_in = lon - si * 30
    return si, ZODIAC[si], deg_in

def get_nakshatra_details(lon):
    lon = normalize_angle(lon)
    nak_index = int(lon // NAKSHATRA_SIZE)
    degrees_into_nakshatra = lon - nak_index * NAKSHATRA_SIZE
    pada = min(4, int(degrees_into_nakshatra // PADA_SIZE) + 1)
    return {
        "name": NAKSHATRA_NAMES[nak_index],
        "index": nak_index + 1,
        "lord": NAKSHATRA_LORDS[nak_index],
        "pada": pada,
        "degrees_in_nakshatra": round(degrees_into_nakshatra, 6),
    }

def get_divisional_chart_start_sign(sign_index, division):
    sign_index = int(sign_index) % 12
    if division == 9:
        if sign_index in {0, 3, 6, 9}:  # movable
            return sign_index
        if sign_index in {1, 4, 7, 10}:  # fixed
            return (sign_index + 8) % 12
        return (sign_index + 4) % 12  # dual
    if division == 10:
        if (sign_index + 1) % 2 == 1:  # odd signs
            return sign_index
        return (sign_index + 8) % 12  # even signs start from 9th
    raise ValueError(f"Unsupported divisional chart division: {division}")

def get_divisional_longitude(lon, division):
    lon = normalize_angle(lon)
    sign_index, _, degree_in_sign = zodiac_sign_from_longitude(lon)
    segment_size = 30.0 / float(division)
    segment_index = min(int(degree_in_sign // segment_size), int(division) - 1)
    start_sign = get_divisional_chart_start_sign(sign_index, division)
    divisional_sign_index = (start_sign + segment_index) % 12
    degree_in_segment = degree_in_sign - segment_index * segment_size
    divisional_degree_in_sign = (degree_in_segment / segment_size) * 30.0
    return normalize_angle(divisional_sign_index * 30.0 + divisional_degree_in_sign)

def build_divisional_chart(chart_code, asc_longitude, planets_out):
    meta = DIVISIONAL_CHART_META[chart_code]
    division = meta["division"]
    asc_div_lon = get_divisional_longitude(asc_longitude, division)
    asc_sign_index, asc_sign_name, asc_degree_in_sign = zodiac_sign_from_longitude(asc_div_lon)
    asc_sign_start = asc_sign_index * 30.0
    cusps_used = [normalize_angle(asc_sign_start + i * 30.0) for i in range(12)]

    planets = []
    for planet in planets_out:
        if "error" in planet:
            continue
        divisional_lon = get_divisional_longitude(planet["longitude_deg"], division)
        sign_index, sign_name, degree_in_sign = zodiac_sign_from_longitude(divisional_lon)
        planets.append({
            "name": planet["name"],
            "longitude_deg": round(divisional_lon, 6),
            "sign": sign_name,
            "sign_index": sign_index + 1,
            "degree_in_sign": round(degree_in_sign, 6),
            "house": get_house_for_longitude(divisional_lon, cusps_used),
            "retrograde": planet.get("retrograde", False),
            "source_longitude_deg": planet["longitude_deg"],
            "source_sign": planet["sign"],
            "source_house": planet["house"],
        })

    return {
        "chart": chart_code,
        "name": meta["name"],
        "division": division,
        "purpose": meta["purpose"],
        "house_system": "Whole Sign",
        "ascendant": {
            "longitude_deg": round(asc_div_lon, 6),
            "sign": asc_sign_name,
            "sign_index": asc_sign_index + 1,
            "degree_in_sign": round(asc_degree_in_sign, 6),
        },
        "house_cusps_deg": build_house_cusps_dict(cusps_used),
        "house_lords": {
            str(house_no): data
            for house_no, data in build_house_lords(cusps_used).items()
        },
        "planets": planets,
    }

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


def ordinal(n):
    if 10 <= (n % 100) <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def canonical_vedic_planet_name(planet_name):
    if planet_name in {"TrueNode", "MeanNode"}:
        return "Rahu"
    return planet_name


def get_planetary_aspect_offsets(planet_name):
    canonical = canonical_vedic_planet_name(planet_name)
    return PLANETARY_ASPECTS.get(canonical, {7})


def get_aspect_type(planet_name, distance):
    canonical = canonical_vedic_planet_name(planet_name)
    if distance not in get_planetary_aspect_offsets(canonical):
        return None
    if distance == 7:
        return "standard"
    if canonical in {"Mars", "Jupiter", "Saturn"}:
        return "special"
    return "standard"


def house_from_offset(source_house, offset):
    return ((int(source_house) + int(offset) - 2) % 12) + 1


def is_within_degree_range(value, start_deg, end_deg):
    value = float(value)
    return start_deg <= value < end_deg or (end_deg == 30.0 and value <= end_deg)


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


def get_combustion_threshold(planet_name, retrograde=False):
    threshold = COMBUSTION_THRESHOLDS.get(planet_name)
    if isinstance(threshold, dict):
        return threshold["retrograde"] if retrograde else threshold["direct"]
    return threshold


def classify_dignity(planet):
    planet_name = planet["name"]
    if planet_name not in EXALTATION_SIGNS:
        return {
            "status": "not_applicable",
            "is_exalted": False,
            "is_debilitated": False,
            "is_own_sign": False,
            "is_moolatrikona": False,
        }

    sign_name = planet["sign"]
    degree_in_sign = float(planet["degree_in_sign"])
    exaltation = EXALTATION_SIGNS[planet_name]
    debilitation = DEBILITATION_SIGNS[planet_name]
    moolatrikona = MOOLATRIKONA_RANGES[planet_name]

    is_exalted = sign_name == exaltation["sign"]
    is_debilitated = sign_name == debilitation["sign"]
    is_moolatrikona = (
        sign_name == moolatrikona["sign"]
        and is_within_degree_range(degree_in_sign, moolatrikona["start_deg"], moolatrikona["end_deg"])
    )
    is_own_sign = sign_name in OWN_SIGNS.get(planet_name, set())

    if is_exalted:
        status = "exalted"
    elif is_debilitated:
        status = "debilitated"
    elif is_moolatrikona:
        status = "moolatrikona"
    elif is_own_sign:
        status = "own_sign"
    else:
        status = "ordinary"

    return {
        "status": status,
        "is_exalted": is_exalted,
        "is_debilitated": is_debilitated,
        "is_own_sign": is_own_sign,
        "is_moolatrikona": is_moolatrikona,
        "exaltation_sign": exaltation["sign"],
        "debilitation_sign": debilitation["sign"],
    }


def classify_combustion(planet, sun):
    planet_name = planet["name"]
    if planet_name == "Sun":
        return {
            "is_combust": False,
            "distance_from_sun_deg": 0.0,
            "threshold_deg": None,
            "status": "not_applicable",
        }
    threshold = get_combustion_threshold(planet_name, retrograde=planet.get("retrograde", False))
    if threshold is None or not sun:
        return {
            "is_combust": False,
            "distance_from_sun_deg": None,
            "threshold_deg": threshold,
            "status": "not_applicable",
        }

    distance = round(angle_distance(planet["longitude_deg"], sun["longitude_deg"]), 3)
    is_combust = distance <= float(threshold)
    return {
        "is_combust": is_combust,
        "distance_from_sun_deg": distance,
        "threshold_deg": float(threshold),
        "status": "combust" if is_combust else "not_combust",
    }


def classify_functional_nature(planet_name, ruled_houses):
    houses = sorted(ruled_houses.get(planet_name, []))
    if not houses:
        return {
            "status": "not_applicable",
            "ruled_houses": [],
            "score": None,
            "notes": [],
        }

    score = sum(FUNCTIONAL_HOUSE_SCORES.get(house, 0) for house in houses)
    notes = []
    if 1 in houses:
        notes.append("Lagna lordship supports functional beneficence")
        score += 1
    if any(house in {5, 9} for house in houses):
        notes.append("Trikona lordship supports benefic results")
    if any(house in {3, 6, 8, 11} for house in houses):
        notes.append("Dusthana/upachaya lordship adds functional malefic influence")
    if any(house in {2, 7} for house in houses):
        notes.append("Maraka lordship adds mixed or challenging results")

    if score >= 3:
        status = "functional_benefic"
    elif score <= -2:
        status = "functional_malefic"
    else:
        status = "mixed"

    return {
        "status": status,
        "ruled_houses": houses,
        "score": score,
        "notes": notes,
    }


def build_planetary_conditions(cusps_used, planets_out):
    house_lords = build_house_lords(cusps_used)
    ruled_houses = build_ruled_houses_map(house_lords)
    planet_map = {planet["name"]: planet for planet in planets_out if "error" not in planet}
    sun = planet_map.get("Sun")
    conditions = {}

    for planet in planets_out:
        planet_name = planet.get("name")
        if "error" in planet:
            continue
        canonical_name = canonical_vedic_planet_name(planet_name)
        dignity = classify_dignity(planet)
        combustion = classify_combustion(planet, sun)
        functional = classify_functional_nature(canonical_name, ruled_houses)
        conditions[planet_name] = {
            "dignity": dignity,
            "combustion": combustion,
            "functional_nature": functional,
        }

    # Ketu uses the same sign axis as Rahu for combustion not applicable and no functional lordship.
    if "TrueNode" in planet_map or "MeanNode" in planet_map:
        node_name = "TrueNode" if "TrueNode" in planet_map else "MeanNode"
        conditions[node_name]["dignity"] = {
            "status": "not_applicable",
            "is_exalted": False,
            "is_debilitated": False,
            "is_own_sign": False,
            "is_moolatrikona": False,
        }

    return conditions


def has_planetary_aspect(source_planet, source_house, target_house):
    return house_distance(source_house, target_house) in get_planetary_aspect_offsets(source_planet)


def build_vedic_planet_map(planets_out, cusps_used):
    planet_map = {planet["name"]: planet for planet in planets_out if "error" not in planet}
    vedic_map = {}

    for planet_name in CLASSICAL_PLANETS:
        planet = planet_map.get(planet_name)
        if not planet:
            continue
        vedic_map[planet_name] = {
            "name": planet_name,
            "source_name": planet_name,
            "longitude_deg": planet["longitude_deg"],
            "sign": planet["sign"],
            "sign_index": planet["sign_index"],
            "house": planet["house"],
            "retrograde": planet["retrograde"],
        }

    node = planet_map.get("TrueNode") or planet_map.get("MeanNode")
    if node:
        vedic_map["Rahu"] = {
            "name": "Rahu",
            "source_name": node["name"],
            "longitude_deg": node["longitude_deg"],
            "sign": node["sign"],
            "sign_index": node["sign_index"],
            "house": node["house"],
            "retrograde": node["retrograde"],
        }

        ketu_lon = normalize_angle(node["longitude_deg"] + 180.0)
        ketu_sign_index, ketu_sign_name, _ = zodiac_sign_from_longitude(ketu_lon)
        vedic_map["Ketu"] = {
            "name": "Ketu",
            "source_name": node["name"],
            "derived_from": node["name"],
            "longitude_deg": round(ketu_lon, 6),
            "sign": ketu_sign_name,
            "sign_index": ketu_sign_index + 1,
            "house": get_house_for_longitude(ketu_lon, cusps_used),
            "retrograde": node["retrograde"],
        }

    return vedic_map


def compute_vedic_aspects(cusps_used, planets_out):
    house_lords = build_house_lords(cusps_used)
    vedic_planet_map = build_vedic_planet_map(planets_out, cusps_used)
    house_to_planets = {}
    for planet_name, planet in vedic_planet_map.items():
        house_to_planets.setdefault(planet["house"], []).append(planet_name)

    by_planet = {}
    flat_aspects = []
    planet_to_planet = []

    for planet_name in VEDIC_PLANETS:
        planet = vedic_planet_map.get(planet_name)
        if not planet:
            continue

        aspects = []
        for distance in sorted(get_planetary_aspect_offsets(planet_name)):
            target_house = house_from_offset(planet["house"], distance)
            target_sign = house_lords[target_house]["sign"]
            aspect_type = get_aspect_type(planet_name, distance)
            target_planets = sorted(house_to_planets.get(target_house, []))
            aspect = {
                "target_house": target_house,
                "target_sign": target_sign,
                "distance": distance,
                "aspect_name": f"{ordinal(distance)}-house aspect",
                "aspect_type": aspect_type,
                "target_planets": target_planets,
            }
            aspects.append(aspect)
            flat_aspects.append({
                "from": planet_name,
                "to_house": target_house,
                "to_sign": target_sign,
                "distance": distance,
                "aspect_name": aspect["aspect_name"],
                "aspect_type": aspect_type,
                "target_planets": target_planets,
            })
            for target_planet in target_planets:
                planet_to_planet.append({
                    "from": planet_name,
                    "to": target_planet,
                    "to_house": target_house,
                    "distance": distance,
                    "aspect_name": aspect["aspect_name"],
                    "aspect_type": aspect_type,
                })

        by_planet[planet_name] = {
            "source_name": planet.get("source_name", planet_name),
            "house": planet["house"],
            "sign": planet["sign"],
            "sign_index": planet["sign_index"],
            "retrograde": planet["retrograde"],
            "aspects": aspects,
        }
        if planet_name == "Ketu" and planet.get("derived_from"):
            by_planet[planet_name]["derived_from"] = planet["derived_from"]

    return {
        "node_basis": "TrueNode" if "Rahu" in by_planet and by_planet["Rahu"]["source_name"] == "TrueNode" else (
            "MeanNode" if "Rahu" in by_planet and by_planet["Rahu"]["source_name"] == "MeanNode" else None
        ),
        "house_signs": {
            str(house_no): {
                "sign": data["sign"],
                "sign_index": data["sign_index"],
            }
            for house_no, data in house_lords.items()
        },
        "by_planet": by_planet,
        "house_aspects": flat_aspects,
        "planet_to_planet": planet_to_planet,
    }


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
    moon_nakshatra = get_nakshatra_details(moon_lon_sid)

    first_lord = moon_nakshatra["lord"]

    frac_into = (moon_lon_sid % NAKSHATRA_SIZE) / NAKSHATRA_SIZE
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
        "moon_nakshatra": moon_nakshatra,
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
            nakshatra = get_nakshatra_details(lon_deg)
            house_no = get_house_for_longitude(lon_deg, cusps_used)
            planets_out.append({
                "name": pname,
                "longitude_deg": round(lon_deg, 6),
                "latitude_deg": round(lat_deg, 6),
                "distance_au": round(dist, 6) if dist is not None else None,
                "sign": sign_name,
                "sign_index": sign_idx + 1,
                "degree_in_sign": round(deg_in_sign, 6),
                "nakshatra": nakshatra,
                "house": house_no,
                "retrograde": bool(retro)
            })
        except Exception as e:
            planets_out.append({"name": pname, "error": str(e)})

    condition_data = build_planetary_conditions(cusps_used, planets_out)
    for planet in planets_out:
        if "error" in planet:
            continue
        planet["conditions"] = condition_data.get(planet["name"], {})

    dasha_data = calc_vimshottari_dasha(jd_ut_local)
    yoga_data = detect_yogas(cusps_used, planets_out)
    aspect_data = compute_vedic_aspects(cusps_used, planets_out)
    divisional_charts = {
        chart_code: build_divisional_chart(chart_code, asc_sid, planets_out)
        for chart_code in DIVISIONAL_CHART_META
    }

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
        "janma_nakshatra": dasha_data.get("moon_nakshatra"),
        "planets": planets_out,
        "planetary_conditions": condition_data,
        "vedic_aspects": aspect_data,
        "yoga_analysis": yoga_data,
        "current_dasha": dasha_data["current"],
        "vimshottari_dasha": dasha_data,
        "divisional_charts": divisional_charts,
        # "notes": f"House system: {'Whole-Sign' if str(house_system).upper().startswith('W') else 'Placidus'} | Sidereal (Lahiri)"
    }
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
