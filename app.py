from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
from orbit_utils import (
    bearing_degrees,
    cardinal_direction,
    distance_km,
    get_iss_tle,
    teme_to_latlon,
)
from sgp4.api import Satrec, jday
from datetime import datetime, timedelta
from math import sqrt, radians, sin, cos, atan2, degrees
from cache_utils import load_cache, save_cache

app = Flask(__name__, template_folder=".")
CORS(app)

@app.route("/")
def index():
    return render_template("index.html")


# ===========================
#  LIVE ISS POSITION
# ===========================
@app.route("/api/get_iss_position")
def get_iss_position():

    # --- Primary: same SGP4 engine used by trajectory/pass calculations ---
    try:
        line1, line2 = get_iss_tle()
        sat = Satrec.twoline2rv(line1, line2)
        now = datetime.utcnow()
        jd, fr = jday(
            now.year,
            now.month,
            now.day,
            now.hour,
            now.minute,
            now.second + now.microsecond / 1_000_000,
        )
        e, r, v = sat.sgp4(jd, fr)
        if e == 0:
            lat, lon = teme_to_latlon(r, now)
            return jsonify({
                "latitude": lat,
                "longitude": lon,
                "source": "sgp4"
            })
    except:
        pass

    # --- Fallback 1: WhereTheISS.at ---
    try:
        resp = requests.get(
            "https://api.wheretheiss.at/v1/satellites/25544",
            timeout=3
        )
        if resp.status_code == 200:
            data = resp.json()
            return jsonify({
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "source": "wheretheiss"
            })
    except:
        pass

    # --- Fallback 2: Open Notify ---
    try:
        resp = requests.get("http://api.open-notify.org/iss-now.json", timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            return jsonify({
                "latitude": float(data["iss_position"]["latitude"]),
                "longitude": float(data["iss_position"]["longitude"]),
                "source": "open-notify"
            })
    except:
        pass

    return jsonify({"error": "Unable to fetch ISS position"}), 503



# ===========================
#  NEXT PASS (A + B)
# ===========================
@app.route("/api/iss-pass")
def iss_pass():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    min_elevation = request.args.get("min_elevation", default=10.0, type=float)

    if lat is None or lon is None:
        return jsonify({"error": "lat and lon are required"}), 400

    cache_key = f"pass_{round(lat,2)}_{round(lon,2)}_{round(min_elevation,1)}"
    cache = load_cache()
    if cache and cache_key in cache:
        return jsonify(cache[cache_key])

    line1, line2 = get_iss_tle()
    sat = Satrec.twoline2rv(line1, line2)

    Re = 6371.0
    now = datetime.utcnow()

    in_pass = False
    pass_start = None
    pass_end = None
    max_elev = None
    max_elev_time = None
    max_elev_lat = None
    max_elev_lon = None
    closest_dist = None

    t = now
    for _ in range(0, 86400, 10):
        jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute, t.second)
        e, r, v = sat.sgp4(jd, fr)
        if e != 0:
            t += timedelta(seconds=10)
            continue

        x, y, z = r
        R = sqrt(x*x + y*y + z*z)
        alt_km = R - Re

        iss_lat, iss_lon = teme_to_latlon(r, t)
        d = distance_km(lat, lon, iss_lat, iss_lon)

        c = d / Re
        if c == 0:
            elev_deg = 90.0
        else:
            num = (Re + alt_km) * cos(c) - Re
            den = (Re + alt_km) * sin(c)
            elev_deg = degrees(atan2(num, den))

        if elev_deg >= min_elevation:
            if not in_pass:
                in_pass = True
                pass_start = t
                max_elev = elev_deg
                max_elev_time = t
                max_elev_lat = iss_lat
                max_elev_lon = iss_lon
                closest_dist = d
            else:
                if elev_deg > max_elev:
                    max_elev = elev_deg
                    max_elev_time = t
                    max_elev_lat = iss_lat
                    max_elev_lon = iss_lon
                if closest_dist is None or d < closest_dist:
                    closest_dist = d
        else:
            if in_pass:
                pass_end = t
                break

        t += timedelta(seconds=10)

    if not in_pass or pass_start is None or pass_end is None:
        return jsonify({"error": "No ISS pass in next 24h"}), 404

    duration = int((pass_end - pass_start).total_seconds())
    look_bearing = bearing_degrees(lat, lon, max_elev_lat, max_elev_lon)

    result = {
        "time": pass_start.strftime("%Y-%m-%d %H:%M:%S"),
        "duration": duration,
        "min_elevation_deg": round(min_elevation, 1),
        "max_elevation_deg": round(max_elev, 1),
        "closest_distance_km": round(closest_dist, 1),
        "peak_time": max_elev_time.strftime("%Y-%m-%d %H:%M:%S"),
        "peak_iss_lat": round(max_elev_lat, 4),
        "peak_iss_lon": round(max_elev_lon, 4),
        "look_bearing_deg": round(look_bearing, 1),
        "look_direction": cardinal_direction(look_bearing)
    }

    save_cache({cache_key: result})
    return jsonify(result)


# ===========================
#  NEXT PASS ISS PREDICTION
# ===========================
@app.route("/api/closest-pass")
def closest_pass():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    hours = request.args.get("hours", default=24, type=int)

    if lat is None or lon is None:
        return jsonify({"error": "lat and lon are required"}), 400
    if hours < 1 or hours > 168:
        return jsonify({"error": "hours must be between 1 and 168"}), 400

    # 1. Intentar usar caché
    cache_key = f"closest_{round(lat,2)}_{round(lon,2)}_{hours}h"
    cache = load_cache()
    if cache and cache_key in cache:
        return jsonify(cache[cache_key])

    # 2. Calcular desde cero
    try:
        line1, line2 = get_iss_tle()
        sat = Satrec.twoline2rv(line1, line2)
    except Exception as ex:
        return jsonify({"error": f"Unable to fetch TLE: {ex}"}), 503

    now = datetime.utcnow()

    closest_dist = None
    closest_time = None
    closest_lat = None
    closest_lon = None
    closest_elev = None

    Re = 6371.0
    t = now
    for _ in range(0, hours * 3600, 10):
        jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute, t.second)
        e, r, v = sat.sgp4(jd, fr)
        if e != 0:
            t += timedelta(seconds=10)
            continue

        x, y, z = r
        R = sqrt(x*x + y*y + z*z)
        alt_km = R - Re

        iss_lat, iss_lon = teme_to_latlon(r, t)
        d = distance_km(lat, lon, iss_lat, iss_lon)
        c = d / Re
        if c == 0:
            elev_deg = 90.0
        else:
            num = (Re + alt_km) * cos(c) - Re
            den = (Re + alt_km) * sin(c)
            elev_deg = degrees(atan2(num, den))

        if closest_dist is None or d < closest_dist:
            closest_dist = d
            closest_time = t
            closest_lat = iss_lat
            closest_lon = iss_lon
            closest_elev = elev_deg

        t += timedelta(seconds=10)

    if closest_dist is None:
        return jsonify({"error": "Unable to compute closest pass"}), 500

    result = {
        "time": closest_time.strftime("%Y-%m-%d %H:%M:%S"),
        "distance_km": round(closest_dist, 1),
        "elevation_deg": round(closest_elev, 1),
        "search_hours": hours,
        "iss_lat": round(closest_lat, 4),
        "iss_lon": round(closest_lon, 4)
    }

    # 3. Guardar en caché
    save_cache({cache_key: result})

    # 4. Devolver
    return jsonify(result)


@app.route("/api/trajectory")
def trajectory():
    minutes = request.args.get("minutes", default=90, type=int)
    step = request.args.get("step", default=60, type=int)

    line1, line2 = get_iss_tle()
    sat = Satrec.twoline2rv(line1, line2)

    now = datetime.utcnow()
    points = []

    t = now
    for _ in range(0, minutes * 60, step):
        jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute, t.second)
        e, r, v = sat.sgp4(jd, fr)
        if e == 0:
            lat, lon = teme_to_latlon(r, t)
            points.append({
                "time": t.strftime("%Y-%m-%d %H:%M:%S"),
                "lat": round(lat, 4),
                "lon": round(lon, 4)
            })
        t += timedelta(seconds=step)

    result = {"points": points}
    return jsonify(result)


# ===========================
#  ASSETS
# ===========================
@app.route('/assets/<path:path>')
def send_assets(path):
    return send_from_directory('assets', path)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
