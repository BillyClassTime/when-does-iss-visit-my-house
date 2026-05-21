from sgp4.api import Satrec, jday
from datetime import datetime, timedelta
from math import atan2, asin, sqrt, degrees, radians, sin, cos, acos
from cache_utils import load_cache, save_cache

import requests

CELESTRAK_TLE_URL = "https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=TLE"
TLE_TTL_HOURS = 6


from cache_utils import load_cache, save_cache

def get_iss_tle():
    cache = load_cache()
    if cache and "tle" in cache:
        fetched_at = cache["tle"].get("fetched_at")
        if fetched_at:
            try:
                age = datetime.utcnow() - datetime.fromisoformat(fetched_at)
                if age <= timedelta(hours=TLE_TTL_HOURS):
                    return cache["tle"]["line1"], cache["tle"]["line2"]
            except ValueError:
                pass

    # si no hay cache → descargar
    resp = requests.get(CELESTRAK_TLE_URL, timeout=5)
    resp.raise_for_status()

    lines = resp.text.strip().splitlines()
    if len(lines) < 3:
        raise RuntimeError("Invalid TLE format received")

    line1 = lines[1].strip()
    line2 = lines[2].strip()

    save_cache({
        "tle": {
            "line1": line1,
            "line2": line2,
            "fetched_at": datetime.utcnow().isoformat()
        }
    })

    return line1, line2




def _gmst_degrees(when):
    jd, fr = jday(
        when.year,
        when.month,
        when.day,
        when.hour,
        when.minute,
        when.second + when.microsecond / 1_000_000,
    )
    days_since_j2000 = (jd + fr) - 2451545.0
    centuries_since_j2000 = days_since_j2000 / 36525.0
    gmst = (
        280.46061837
        + 360.98564736629 * days_since_j2000
        + 0.000387933 * centuries_since_j2000 * centuries_since_j2000
        - (centuries_since_j2000 ** 3) / 38710000.0
    )
    return gmst % 360.0


def _normalize_lon(lon):
    return ((lon + 180.0) % 360.0) - 180.0


def teme_to_latlon(r, when=None):
    if when is None:
        when = datetime.utcnow()

    x, y, z = r
    R = sqrt(x*x + y*y + z*z)
    lat = asin(z / R)
    inertial_lon = degrees(atan2(y, x))
    lon = _normalize_lon(inertial_lon - _gmst_degrees(when))
    return degrees(lat), lon


def distance_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    return 6371 * acos(
        sin(lat1)*sin(lat2) +
        cos(lat1)*cos(lat2)*cos(lon2 - lon1)
    )


def bearing_degrees(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    y = sin(dlon) * cos(lat2)
    x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
    return (degrees(atan2(y, x)) + 360) % 360


def cardinal_direction(bearing):
    directions = [
        "N", "NNE", "NE", "ENE",
        "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW",
        "W", "WNW", "NW", "NNW",
    ]
    index = round(bearing / 22.5) % 16
    return directions[index]
