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


# ---------------- Vimshottari Dasha ----------------
def calc_vimshottari_dasha(jd_ut):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    xx, _ = swe.calc_ut(jd_ut, swe.MOON, swe.FLG_SIDEREAL)
    moon_lon_sid = normalize_angle(xx[0])

    nak_size = 360.0/27.0
    nak_index = int(moon_lon_sid // nak_size)
    first_lord = NAKSHATRA_LORDS[nak_index]

    frac_into = (moon_lon_sid % nak_size) / nak_size
    frac_left = 1.0 - frac_into
    balance_years = frac_left * DASHA_YEARS[first_lord]

    now_utc = datetime.now(tz=pytz.UTC)
    today_jd = swe.julday(now_utc.year, now_utc.month, now_utc.day,
                         now_utc.hour + now_utc.minute/60.0 + now_utc.second/3600.0 + now_utc.microsecond/3600.0/1e6)

    dasha_list = []
    idx = DASHA_ORDER.index(first_lord)
    start_jd = jd_ut
    i = 0
    while True:
        p = DASHA_ORDER[(idx + i) % 9]
        years = balance_years if i == 0 else DASHA_YEARS[p]
        end_jd = start_jd + years * DAYS_PER_YEAR
        dasha_list.append({"planet": p, "start_jd": start_jd, "end_jd": end_jd})
        if end_jd >= today_jd:
            break
        start_jd = end_jd
        i += 1
        if i > 1000:
            break

    current_maha = next((d for d in dasha_list if d["start_jd"] <= today_jd < d["end_jd"]), None)

    current_anta = None
    if current_maha:
        maha_start = current_maha["start_jd"]
        maha_end = current_maha["end_jd"]
        maha_years_effective = (maha_end - maha_start) / DAYS_PER_YEAR
        idx2 = DASHA_ORDER.index(current_maha["planet"])
        start_sub = maha_start
        for j in range(9):
            p = DASHA_ORDER[(idx2 + j) % 9]
            anta_years = maha_years_effective * (DASHA_YEARS[p] / 120.0)
            end_sub = start_sub + anta_years * DAYS_PER_YEAR
            if start_sub <= today_jd < end_sub:
                current_anta = {"planet": p, "start_jd": start_sub, "end_jd": end_sub}
                break
            start_sub = end_sub

    def ser(d):
        if not d: return None
        return {"planet": d["planet"], "start": jd_to_iso(d["start_jd"]), "end": jd_to_iso(d["end_jd"])}
    return ser(current_maha), ser(current_anta)


# --------------- Main generator ---------------
def generate_chart(birth, house_system='P'):
    required = ["year","month","day","hour","minute","second","timezone","latitude","longitude"]
    for k in required:
        if k not in birth:
            raise ValueError(f"Missing {k}")

    tz = pytz.timezone(birth["timezone"])
    local_dt = datetime(birth["year"], birth["month"], birth["day"],
                        birth["hour"], birth["minute"], birth["second"])
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

    maha, anta = calc_vimshottari_dasha(jd_ut_local)

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
        "current_dasha": {"mahadasha": maha, "antardasha": anta},
        "notes": f"House system: {'Whole-Sign' if str(house_system).upper().startswith('W') else 'Placidus'} | Sidereal (Lahiri)"
    }
    return json.dumps(out, indent=2)


# --------------- Demo ----------------
if __name__ == "__main__":
    sample = {
        "year": 2001, "month": 8, "day": 14,
        "hour": 2, "minute": 30, "second": 0,
        "timezone": "Asia/Kolkata",
        "latitude": 24.5362, "longitude": 81.29911, "altitude_m": 216
    }
    print(generate_chart(sample, house_system="WS"))
