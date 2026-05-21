import json
import os
from datetime import datetime, timedelta

CACHE_FILE = "cache.json"
CACHE_TTL_HOURS = 1  # tiempo de vida del cache

def load_cache():
    if not os.path.exists(CACHE_FILE):
        return None

    try:
        with open(CACHE_FILE, "r") as f:
            data = json.load(f)

        ts = datetime.fromisoformat(data.get("timestamp"))
        if datetime.utcnow() - ts > timedelta(hours=CACHE_TTL_HOURS):
            return None  # expirado

        return data

    except:
        return None


def save_cache(new_data):
    # Cargar el cache actual para no borrar lo que ya existe
    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cache = json.load(f)
        except:
            cache = {}

    # Actualizar con los nuevos datos
    cache.update(new_data)
    cache["timestamp"] = datetime.utcnow().isoformat()

    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)