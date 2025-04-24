# Quick Path - Shortest Route Web App

This project is a Flask-based web app that lets you find the shortest route between two places using a local OSM file.

## 🛠 Features

- Uses Dijkstra's Algorithm from scratch
- Local OSM file for map data (no Overpass API)
- Geocoding via Nominatim
- Visualizes routes with Folium

## 📦 Requirements

- Python 3.7+
- See `requirements.txt` for dependencies

## 🚀 How to Run

1. Clone the repository:
    ```
    git clone https://github.com/RootGaurav/DS_Project.git
    
    ```

2. (Optional) Create a virtual environment:
    ```
    python -m venv venv
    venv\Scripts\activate   # On Windows
    ```

3. Install dependencies:
    ```
    pip install -r requirements.txt
    ```

4. Run the app:
    ```
    python app.py
    ```

5. Open your browser and visit:
    ```
    http://127.0.0.1:5000/
    ```


