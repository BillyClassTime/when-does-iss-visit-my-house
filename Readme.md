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
* **APIs:** Open Notify API for real-time telemetry data data sync.

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


---

## 💙 Acknowledgements and Credits

This fun project would not have been the same without the following tools, which helped to bring its visual identity to life:

* 🎬 **[deevid.ai](https://deevid.ai)** – For generating the incredible video that brought our ISS into action.
* 🤖 **Gemini (Google)** – For co-creating the initial illustration and artwork of our cheeky, rogue ISS.
* ⚙️ **[ezgif.com](https://ezgif.com)** – For the optimization tools and the flawless conversion into an animated web format (GIF) whilst preserving quality.
* 🪄 **[remove.bg](https://www.remove.bg)** – For its superb AI that stripped away the original background in seconds.
* 🎨 **[Photopea](https://www.photopea.com)** – For providing a powerful, browser-based editor that let us trim the canvas and perform some DIY digital surgery.
---