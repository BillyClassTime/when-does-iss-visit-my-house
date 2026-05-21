from flask import Flask, render_template, request, jsonify
import requests
import os
from orbit_utils import get_iss_tle, teme_to_latlon, distance_km
from sgp4.api import Satrec, jday
from datetime import datetime, timedelta
from math import sqrt, radians, sin, cos, atan2, degrees
from cache_utils import load_cache, save_cache

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")


# ===========================
#  LIVE ISS POSITION
# ===========================
@app.route("/get_iss_position")
def get_iss_position():

    # --- Primary API: WhereTheISS.at ---
    try:
        resp = requests.get(
            "https://api.wheretheiss.at/v1/satellites/25544",
            timeout=3
        )
        if resp.status_code == 200:
            data = resp.json()
            return jsonify({
                "latitude": data["latitude"],
                "longitude": data["longitude"]
            })
    except:
        pass

    # --- Fallback 1: Open Notify ---
    try:
        resp = requests.get("http://api.open-notify.org/iss-now.json", timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            return jsonify({
                "latitude": float(data["iss_position"]["latitude"]),
                "longitude": float(data["iss_position"]["longitude"])
            })
    except:
        pass

    # --- Fallback 2: SGP4 Prediction (Offline/API Failure) ---
    try:
        line1, line2 = get_iss_tle()
        sat = Satrec.twoline2rv(line1, line2)
        now = datetime.utcnow()
        jd, fr = jday(now.year, now.month, now.day, now.hour, now.minute, now.second)
        e, r, v = sat.sgp4(jd, fr)
        if e == 0:
            lat, lon = teme_to_latlon(r)
            return jsonify({
                "latitude": lat,
                "longitude": lon,
                "note": "calculated via SGP4"
            })
    except:
        pass

    return jsonify({"error": "Unable to fetch ISS position"}), 503



# ===========================
#  NEXT PASS (A + B)
# ===========================
@app.route("/iss-pass")
def iss_pass():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)

    if lat is None or lon is None:
        return jsonify({"error": "lat and lon are required"}), 400

    cache_key = f"pass_{round(lat,2)}_{round(lon,2)}"
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

        iss_lat, iss_lon = teme_to_latlon(r)
        d = distance_km(lat, lon, iss_lat, iss_lon)

        c = d / Re
        if c == 0:
            elev_deg = 90.0
        else:
            num = (Re + alt_km) * cos(c) - Re
            den = (Re + alt_km) * sin(c)
            elev_deg = degrees(atan2(num, den))

        if elev_deg > 0:
            if not in_pass:
                in_pass = True
                pass_start = t
                max_elev = elev_deg
            else:
                if elev_deg > max_elev:
                    max_elev = elev_deg
        else:
            if in_pass:
                pass_end = t
                break

        t += timedelta(seconds=10)

    if not in_pass or pass_start is None or pass_end is None:
        return jsonify({"error": "No ISS pass in next 24h"}), 404

    duration = int((pass_end - pass_start).total_seconds())

    result = {
        "time": pass_start.strftime("%Y-%m-%d %H:%M:%S"),
        "duration": duration,
        "max_elevation_deg": round(max_elev, 1)
    }

    save_cache({cache_key: result})
    return jsonify(result)


# ===========================
#  NEXT PASS ISS PREDICTION
# ===========================
@app.route("/closest-pass")
def closest_pass():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)

    if lat is None or lon is None:
        return jsonify({"error": "lat and lon are required"}), 400

    # 1. Intentar usar caché
    cache_key = f"closest_{round(lat,2)}_{round(lon,2)}"
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

    t = now
    for _ in range(0, 5400, 10):
        jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute, t.second)
        e, r, v = sat.sgp4(jd, fr)
        if e != 0:
            t += timedelta(seconds=10)
            continue

        iss_lat, iss_lon = teme_to_latlon(r)
        d = distance_km(lat, lon, iss_lat, iss_lon)

        if closest_dist is None or d < closest_dist:
            closest_dist = d
            closest_time = t
            closest_lat = iss_lat
            closest_lon = iss_lon

        t += timedelta(seconds=10)

    if closest_dist is None:
        return jsonify({"error": "Unable to compute closest pass"}), 500

    result = {
        "time": closest_time.strftime("%Y-%m-%d %H:%M:%S"),
        "distance_km": round(closest_dist, 1),
        "iss_lat": round(closest_lat, 4),
        "iss_lon": round(closest_lon, 4)
    }

    # 3. Guardar en caché
    save_cache({cache_key: result})

    # 4. Devolver
    return jsonify(result)


@app.route("/trajectory")
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
            lat, lon = teme_to_latlon(r)
            points.append({
                "time": t.strftime("%Y-%m-%d %H:%M:%S"),
                "lat": round(lat, 4),
                "lon": round(lon, 4)
            })
        t += timedelta(seconds=step)

    result = {"points": points}
    return jsonify(result)


# ===========================
#  FAVICON
# ===========================
@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
