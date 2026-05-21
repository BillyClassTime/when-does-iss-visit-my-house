/* 
===========================
   HOME BUTTON
=========================== */
function goHome() {
    window.location.href = "/";
}

/* 
===========================
   LEAFLET MAP
=========================== */

const map = L.map('map').setView([40.4168, -3.7038], 3);

L.tileLayer(
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    {
        attribution: '&copy; OpenStreetMap contributors'
    }
).addTo(map);

/* 
===========================
   ICONS
=========================== */

// House icon (user location)
const houseIcon = L.icon({
    iconUrl: "https://cdn-icons-png.flaticon.com/512/25/25694.png",
    iconSize: [32, 32],
    iconAnchor: [16, 32]
});

// ISS icon
const issIcon = L.icon({
    iconUrl: "/assets/iss.png",
    iconSize: [52, 52],
    iconAnchor: [26, 26]
});

let marker;     // user house marker
let issMarker;  // ISS marker
let nextVisiblePassMarker; // predicted max-elevation pass marker
let closestApproachMarker; // predicted closest ISS ground-track marker

const ISS_REFRESH_MS = 5000;


/* 
===========================
   SET HOUSE MARKER
=========================== */

function setHouse(lat, lon) {

    // Actualizar inputs
    document.getElementById('lat').value = lat;
    document.getElementById('lon').value = lon;

    // Si ya existe, moverla
    if (marker) {
        marker.setLatLng([lat, lon]);
    } else {
        marker = L.marker([lat, lon], { icon: houseIcon }).addTo(map);
    }

    // Centrar mapa
    map.setView([lat, lon], 6);
}

/* 
===========================
   LIVE ISS POSITION
=========================== */

async function updateISSPosition() {
    try {
        const response = await fetch(`/api/get_iss_position?_=${Date.now()}`, {
            cache: "no-store",
            headers: {
                "Accept": "application/json"
            }
        });

        if (!response.ok) {
            throw new Error(`ISS position request failed with ${response.status}`);
        }

        const data = await response.json();

        if (data.error) {
            console.log("ISS API error:", data.error);
        } else {
            const lat = Number(data.latitude);
            const lon = Number(data.longitude);

            if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
                throw new Error("ISS position response did not include valid coordinates");
            }

            if (issMarker) {
                issMarker.setLatLng([lat, lon]);
            } else {
                issMarker = L.marker([lat, lon], { icon: issIcon }).addTo(map);
                
                // Si no hay casa marcada, centrar mapa en la ISS al inicio
                if (!marker) {
                    map.setView([lat, lon], 4);
                }
            }

            updateISSStatus(lat, lon);
        }

    } catch (err) {
        console.log("ISS position error:", err);
        updateISSStatus(null, null, "ISS telemetry unavailable");
    }

    // Refresh frequently so the marker visibly advances.
    setTimeout(updateISSPosition, ISS_REFRESH_MS);
}

// Start ISS tracking
updateISSPosition();

function updateISSStatus(lat, lon, message) {
    const status = document.getElementById('iss-status');
    if (!status) return;

    if (message) {
        status.textContent = message;
        return;
    }

    const now = new Date().toLocaleTimeString();
    status.textContent = `ISS ${lat.toFixed(4)}, ${lon.toFixed(4)} · ${now}`;
}

/* 
===========================
   CLICK ON MAP (SET HOUSE)
=========================== */

map.on('click', function (e) {
    const lat = e.latlng.lat.toFixed(4);
    const lon = e.latlng.lng.toFixed(4);
    setHouse(lat, lon);
});

/* 
===========================
   INPUT LISTENERS (SET HOUSE)
=========================== */

document.getElementById('lat').addEventListener('change', () => {
    const lat = parseFloat(document.getElementById('lat').value);
    const lon = parseFloat(document.getElementById('lon').value);
    if (!isNaN(lat) && !isNaN(lon)) setHouse(lat, lon);
});

document.getElementById('lon').addEventListener('change', () => {
    const lat = parseFloat(document.getElementById('lat').value);
    const lon = parseFloat(document.getElementById('lon').value);
    if (!isNaN(lat) && !isNaN(lon)) setHouse(lat, lon);
});

/* 
===========================
   ISS PASS FUNCTION
=========================== */

async function getNextPass() {

    const lat = document.getElementById('lat').value;
    const lon = document.getElementById('lon').value;

    const result = document.getElementById('result');

    if (!lat || !lon) {
        result.innerHTML = "⚠ Please select coordinates first.";
        return;
    }

    result.innerHTML = "🛰 Searching next ISS pass...";

    try {
        const response = await fetch(`/api/iss-pass?lat=${lat}&lon=${lon}&min_elevation=10`);
        const data = await response.json();

        if (data.error) {
            result.innerHTML = `❌ ${data.error}`;
            return;
        }

        result.innerHTML =
            `🚀 Next ISS pass:<br><br>
             Starts (UTC): <strong>${data.time}</strong><br>
             Peak (UTC): <strong>${data.peak_time}</strong><br>
             Duration above ${data.min_elevation_deg}°: <strong>${data.duration} seconds</strong><br>
             Max elevation: <strong>${data.max_elevation_deg}°</strong><br>
             Closest ground distance: <strong>${data.closest_distance_km} km</strong><br>
             Look toward: <strong>${data.look_direction} (${data.look_bearing_deg}°)</strong>`;

        showNextVisiblePass(data);

    } catch (error) {
        result.innerHTML = "❌ Error fetching ISS pass data.";
    }
}

function showNextVisiblePass(data) {
    const predictedLat = Number(data.peak_iss_lat);
    const predictedLon = Number(data.peak_iss_lon);

    if (!Number.isFinite(predictedLat) || !Number.isFinite(predictedLon)) {
        return;
    }

    const tooltip = `Next visible pass peak: look ${data.look_direction} (${data.look_bearing_deg}°)`;

    if (nextVisiblePassMarker) {
        nextVisiblePassMarker.setLatLng([predictedLat, predictedLon]);
        nextVisiblePassMarker.setTooltipContent(tooltip);
    } else {
        nextVisiblePassMarker = L.circleMarker([predictedLat, predictedLon], {
            radius: 8,
            color: '#60a5fa',
            weight: 3,
            fillColor: '#2563eb',
            fillOpacity: 0.9
        }).addTo(map);
        nextVisiblePassMarker.bindTooltip(tooltip);
    }
}

/* 
===========================
   ISS PREDICTION CALL
=========================== */
async function getClosestPass() {
    const lat = document.getElementById('lat').value;
    const lon = document.getElementById('lon').value;
    const result = document.getElementById('result');

    if (!lat || !lon) {
        result.innerHTML = "⚠ Please select coordinates first.";
        return;
    }

    result.innerHTML = "🏠 Checking the next 24 hours of ISS ground track...";

    try {
        const response = await fetch(`/api/closest-pass?lat=${lat}&lon=${lon}&hours=24`);
        const data = await response.json();

        if (data.error) {
            result.innerHTML = `❌ ${data.error}`;
            return;
        }

        result.innerHTML =
            `🏠 Roof-track check:<br><br>
             ${describeRoofTrack(data.distance_km)}<br>
             Predicted time (UTC): <strong>${data.time}</strong><br>
             Ground-track distance: <strong>${data.distance_km} km</strong><br>
             Approx elevation: <strong>${data.elevation_deg}°</strong><br>
             Search window: <strong>${data.search_hours} hours</strong><br>
             Predicted ISS ground track: (${data.iss_lat}, ${data.iss_lon})`;

        showClosestApproach(data.iss_lat, data.iss_lon);
    } catch (err) {
        result.innerHTML = "❌ Error computing closest pass.";
    }
}

function showClosestApproach(lat, lon) {
    const predictedLat = Number(lat);
    const predictedLon = Number(lon);

    if (!Number.isFinite(predictedLat) || !Number.isFinite(predictedLon)) {
        return;
    }

    if (closestApproachMarker) {
        closestApproachMarker.setLatLng([predictedLat, predictedLon]);
    } else {
        closestApproachMarker = L.circleMarker([predictedLat, predictedLon], {
            radius: 8,
            color: '#facc15',
            weight: 3,
            fillColor: '#f97316',
            fillOpacity: 0.9
        }).addTo(map);
        closestApproachMarker.bindTooltip('Predicted closest ISS ground track');
    }
}

function describeRoofTrack(distanceKm) {
    if (distanceKm <= 25) {
        return "✅ Yes. Basically over your roof.";
    }

    if (distanceKm <= 100) {
        return "✅ Very close ground-track pass.";
    }

    if (distanceKm <= 500) {
        return "🟡 Nearby ground track, but not over your roof.";
    }

    if (distanceKm <= 1200) {
        return "🌍 Regional fly-by. Interesting, but not a roof pass.";
    }

    return "❌ No roof pass in this search window.";
}


let currentOrbitLayer = null; // Variable global para controlar la trayectoria

function drawOrbit(points) {
    // TRUCO: Si ya existía una línea de órbita en el mapa, la borramos primero
    if (currentOrbitLayer) {
        map.removeLayer(currentOrbitLayer);
    }

    console.log("Raw points for orbit:", points);

    // Convertimos los puntos de la API al formato de Leaflet [lat, lng]
    // La API envía {lat, lon}, así que mapeamos a [p.lat, p.lon]
    const path = points
        .filter(p => {
            const isValid = p.lat !== undefined && p.lon !== undefined && p.lat !== null && p.lon !== null;
            if (!isValid) console.warn("Invalid point detected:", p);
            return isValid;
        })
        .map(p => [Number(p.lat), Number(p.lon)])
        .filter(([lat, lon]) => Number.isFinite(lat) && Number.isFinite(lon));

    console.log("Filtered path for Leaflet:", path);

    if (path.length === 0) {
        console.warn("No valid trajectory points to draw.");
        return;
    }

    const orbitSegments = splitAtAntimeridian(path);
    currentOrbitLayer = L.featureGroup(
        orbitSegments.map(segment => L.polyline(segment, { color: 'yellow', weight: 3 }))
    ).addTo(map);

    // Ajustar mapa
    map.fitBounds(currentOrbitLayer.getBounds(), { padding: [50, 50], animate: true, duration: 1.5 });
}

/* 
===========================
 ISS TRAJECTORY TO MY HOME
=========================== */
async function getTrajectory() {
    const result = document.getElementById('result');
    result.innerHTML = "🛰 Calculating ISS trajectory...";

    try {
        const response = await fetch('/api/trajectory?minutes=90&step=60');
        const data = await response.json();

        if (!data.points) {
            result.innerHTML = "❌ No trajectory data received.";
            return;
        }

        drawOrbit(data.points);

        result.innerHTML = `🛰 Trajectory loaded: ${data.points.length} points`;

    } catch (err) {
        console.log(err);
        result.innerHTML = "❌ Error loading trajectory.";
    }
}

function splitAtAntimeridian(path) {
    const segments = [];
    let current = [];

    for (const point of path) {
        if (current.length > 0) {
            const previous = current[current.length - 1];
            const longitudeJump = Math.abs(point[1] - previous[1]);

            if (longitudeJump > 180) {
                segments.push(current);
                current = [];
            }
        }

        current.push(point);
    }

    if (current.length > 0) {
        segments.push(current);
    }

    return segments;
}
