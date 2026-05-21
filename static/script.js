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
    iconUrl: "https://upload.wikimedia.org/wikipedia/commons/d/d0/International_Space_Station.svg",
    iconSize: [40, 40],
    iconAnchor: [20, 20]
});

let marker;     // user house marker
let issMarker;  // ISS marker

let trajectoryLine = null;


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
        const response = await fetch("/get_iss_position");
        const data = await response.json();

        if (data.error) {
            console.log("ISS API error:", data.error);
        } else {
            const lat = data.latitude;
            const lon = data.longitude;

            if (issMarker) {
                issMarker.setLatLng([lat, lon]);
            } else {
                issMarker = L.marker([lat, lon], { icon: issIcon }).addTo(map);
                
                // Si no hay casa marcada, centrar mapa en la ISS al inicio
                if (!marker) {
                    map.setView([lat, lon], 4);
                }
            }
        }

    } catch (err) {
        console.log("ISS position error:", err);
    }

    // Refresh every 10 seconds (SIEMPRE re-intentar)
    setTimeout(updateISSPosition, 10000);
}

// Start ISS tracking
updateISSPosition();

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
        const response = await fetch(`/iss-pass?lat=${lat}&lon=${lon}`);
        const data = await response.json();

        if (data.error) {
            result.innerHTML = `❌ ${data.error}`;
            return;
        }

        result.innerHTML =
            `🚀 Next ISS pass:<br><br>
             <strong>${data.time}</strong><br>
             Visible for ${data.duration} seconds`;

    } catch (error) {
        result.innerHTML = "❌ Error fetching ISS pass data.";
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

    result.innerHTML = "🛰 Calculating closest ISS approach...";

    try {
        const response = await fetch(`/closest-pass?lat=${lat}&lon=${lon}`);
        const data = await response.json();

        if (data.error) {
            result.innerHTML = `❌ ${data.error}`;
            return;
        }

        result.innerHTML =
            `🛰 Closest ISS approach:<br><br>
             Time: <strong>${data.time}</strong><br>
             Distance: <strong>${data.distance_km} km</strong><br>
             ISS position then: (${data.iss_lat}, ${data.iss_lon})`;
    } catch (err) {
        result.innerHTML = "❌ Error computing closest pass.";
    }
}


/* 
===========================
 ISS TRAJECTORY TO MY HOME
=========================== */
async function getTrajectory() {
    const result = document.getElementById('result');
    result.innerHTML = "🛰 Calculating ISS trajectory...";

    try {
        const response = await fetch('/trajectory?minutes=90&step=60');
        const data = await response.json();

        if (!data.points) {
            result.innerHTML = "❌ No trajectory data received.";
            return;
        }

        // Normalizar longitudes para evitar saltos
        const latlngs = normalizeTrajectory(data.points);

        // Borrar trayectoria anterior
        if (trajectoryLine) {
            map.removeLayer(trajectoryLine);
        }

        // Dibujar polyline
        trajectoryLine = L.polyline(latlngs, {
            color: "yellow",
            weight: 3,
            opacity: 0.8
        }).addTo(map);

        // Ajustar mapa
        map.fitBounds(trajectoryLine.getBounds());

        result.innerHTML = `🛰 Trajectory loaded: ${data.points.length} points`;

    } catch (err) {
        console.log(err);
        result.innerHTML = "❌ Error loading trajectory.";
    }
}


function normalizeTrajectory(points) {
    const fixed = [];
    let prevLon = null;

    for (const p of points) {
        let lon = p.lon;

        if (prevLon !== null) {
            // Detectar salto grande (cruce del meridiano)
            if (Math.abs(lon - prevLon) > 180) {
                if (lon > prevLon) {
                    lon -= 360;
                } else {
                    lon += 360;
                }
            }
        }

        fixed.push([p.lat, lon]);
        prevLon = lon;
    }

    return fixed;
}
