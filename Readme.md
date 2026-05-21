# 🛰️ When Does the ISS Visit My House?

> A delightful, slightly over-engineered tiny tool to predict when the International Space Station flies right over your roof. Built for an audience of one, but open for anyone who looks at the sky with curiosity.

---

## 🗺️ Preview

![ISS Tracker Demo](assets/preview.gif)

---

## ✨ Features

* **Live Tracking:** Watch the ISS cruise across the globe in real-time.
* **Interactive Map:** Click anywhere on the map or type your coordinates to place your little home.
* **Next Fly-by Countdown:** Find out exactly when the space station is going to pass by your location.
* **Roof Check:** Calculate the minimal orbital distance to see if it's literally crossing your roof.
* **Orbit Drawing:** Plot the next 90 orbital points using real-time orbital mechanics.

---

## 🧠 The Tech Stack (Light Orbital Mechanics)

What started as a quick 20-minute idea turned into a midnight coding session because, well... if you build it, you build it right! 

* **Backend:** Flask (Python) handles the math and routing.
* **Orbital Engine:** Integrated with **SGP4** for high-precision mathematical orbital prediction.
* **Frontend:** Clean, space-inspired dark UI built with Leaflet.js and raw CSS.
* **APIs:** Open Notify API and WhereTheISS.at for real-time telemetry data sync.
* **Azure Deployment:** Frontend on Azure Static Web Apps, backend on Azure Container Apps, connected through `staticwebapp.config.json`.

---

## ☁️ Azure Setup

This project is set up as a split deployment:

* The frontend is served from Azure Static Web Apps.
* The backend runs as a Flask app inside Azure Container Apps.
* `staticwebapp.config.json` exposes `/api/*` and proxies those requests to the backend container.

That means the browser-facing calls go through `/api/...`, while the backend can stay as a normal Flask app behind Azure.

---

## 👁️ ISS Visibility: Can I see it from home?

Yes, but **only during dawn or dusk**. For the ISS to be visible to the naked eye, three conditions must be met:
1. **Proximity:** The ISS must pass within a few hundred kilometres of your location.
2. **Darkness:** Your local sky must be dark (nighttime).
3. **Sunlight:** The ISS must be high enough to still be illuminated by the sun, reflecting light off its massive solar panels.

*Note: You can cross-reference our trajectory calculations with NASA's official "Spot The Station" data. While NASA provides the raw telemetry, this Tiny Tool aims to offer a significantly more engaging, streamlined, and modern user interface.*

---

## 🚀 Quick Start (Local Setup)

You can run this tiny tool locally using Docker or directly with Python.

### Option 1: Docker (Recommended)

1. Clone this repository:
   ```bash
   git clone [https://github.com/BillyClassTime/when-does-iss-visit-my-house.git](https://github.com/BillyClassTime/when-does-iss-visit-my-house.git)
   cd when-does-iss-visit-my-house
   ```

2. Build and run the container:
   ```bash
   docker build -t iss-visit-tool .
   docker run -p 8080:8080 iss-visit-tool
   ```

### Option 2: Python

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the app:
   ```bash
   python app.py
   ```
---

### 🛰️ API Endpoints (Direct Backend Production URLs)

You can test the live container app endpoints directly using `curl`:

#### 1. Real-Time ISS Position
Returns the current latitude, longitude, and an orbital math note.
```bash
curl https://ca-iss-backend-usa.orangeriver-813e879f.eastus.azurecontainerapps.io/get_iss_position
```

#### 2. Next ISS Pass Prediction
Calculates the exact time and duration of the next visible pass for a specific location.

```bash
curl "https://ca-iss-backend-usa.orangeriver-813e879f.eastus.azurecontainerapps.io/iss-pass?lat=40.4168&lon=-3.7038"
```

#### 3. Closest Approach Prediction
Computes the precise moment and minimum distance (in km) when the ISS is nearest to you.

```bash
curl "https://ca-iss-backend-usa.orangeriver-813e879f.eastus.azurecontainerapps.io/closest-pass?lat=40.4168&lon=-3.7038"
```

#### 4. Future Orbit Trajectory
Generates an array of geographical points mapping out the complete orbital path for the next 90 minutes.

```bash
curl "https://ca-iss-backend-usa.orangeriver-813e879f.eastus.azurecontainerapps.io/trajectory?minutes=90&step=60"
```



---

## 💙 Acknowledgements and Credits

This fun project would not have been the same without the following tools, which helped to bring its visual identity to life:

* 🎬 **[deevid.ai](https://deevid.ai)** – For generating the incredible video that brought our ISS into action.
* 🤖 **Gemini (Google)** – For co-creating the initial illustration and artwork of our cheeky, rogue ISS.
* ⚙️ **[ezgif.com](https://ezgif.com)** – For the optimization tools and the flawless conversion into an animated web format (GIF) whilst preserving quality.
* 🪄 **[remove.bg](https://www.remove.bg)** – For its superb AI that stripped away the original background in seconds.
* 🎨 **[Photopea](https://www.photopea.com)** – For providing a powerful, browser-based editor that let us trim the canvas and perform some DIY digital surgery.
---
