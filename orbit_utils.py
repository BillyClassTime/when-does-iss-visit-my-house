from sgp4.api import Satrec, jday
from datetime import datetime, timedelta
from math import atan2, asin, sqrt, degrees, radians, sin, cos, acos
from cache_utils import load_cache, save_cache

import requests

CELESTRAK_TLE_URL = "https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=TLE"


from cache_utils import load_cache, save_cache

def get_iss_tle():
    cache = load_cache()
    if cache and "tle" in cache:
        return cache["tle"]["line1"], cache["tle"]["line2"]

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
            "line2": line2
        }
    })

    return line1, line2




def teme_to_latlon(r):
    x, y, z = r
    R = sqrt(x*x + y*y + z*z)
    lat = asin(z / R)
    lon = atan2(y, x)
    return degrees(lat), degrees(lon)


def distance_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    return 6371 * acos(
        sin(lat1)*sin(lat2) +
        cos(lat1)*cos(lat2)*cos(lon2 - lon1)
    )
