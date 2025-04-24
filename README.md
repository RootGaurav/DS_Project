# 🚀 Quick Path - Shortest Path Finder using OSM & Flask

**Quick Path** is a Flask-based web app that allows users to find the **shortest walking route** between two locations (e.g., landmarks, streets) in **Dehradun**, India using a local `.osm` file, Dijkstra's algorithm, and Folium map visualization.

---

## 📸 Preview

- Input: User enters source and destination in a smart dark-themed UI.
- Output: A rendered map showing the shortest path with markers.

---

## 🧰 Features

- Custom location-based pathfinding.
- Dijkstra’s algorithm for shortest path.
- Visual map rendering using Folium.
- Nominatim (OpenStreetMap) for geocoding.
- Local `.osm` file for offline processing (no Overpass needed).
- Clean, dark-themed UI with HTML/CSS.

---


---

It’s recommended to use a virtual environment:

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
