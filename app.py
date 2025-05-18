from flask import Flask, render_template, request, redirect, url_for
import os, xmltodict, folium, heapq, joblib
from geopy.geocoders import Nominatim
from scipy.spatial import KDTree
from collections import defaultdict
import random

app = Flask(__name__)
cache_dir = "cache"
os.makedirs(cache_dir, exist_ok=True)

# Preprocessing or loading cached data
if all(os.path.exists(f"{cache_dir}/{f}") for f in ["graph.pkl", "xy.pkl", "original_ids.pkl"]):
    adj_list = joblib.load(f"{cache_dir}/graph.pkl")
    xy = joblib.load(f"{cache_dir}/xy.pkl")
    original_ids = joblib.load(f"{cache_dir}/original_ids.pkl")
    orig2small = {nid: idx for idx, nid in enumerate(original_ids)}
    small2orig = {idx: nid for idx, nid in enumerate(original_ids)}
else:
    with open("Maps/map.osm", "rb") as f:
        osm = xmltodict.parse(f)["osm"]

    road_vals = {
        'motorway', 'trunk', 'primary', 'secondary', 'tertiary',
        'residential', 'living_street', 'service', 'unclassified',
        'road', 'track', 'path'
    }

    ways = []
    road_node_ids = set()
    Way = osm.get('way', [])
    if not isinstance(Way, list): Way = [Way]
    for way in Way:
        tags = way.get('tag', [])
        if isinstance(tags, dict): tags = [tags]
        if not any(tag['@k'] == 'highway' and tag['@v'] in road_vals for tag in tags):
            continue
        nodes = [int(nd['@ref']) for nd in way.get('nd', []) if '@ref' in nd]
        if len(nodes) >= 2:
            ways.append(nodes)
            road_node_ids.update(nodes)

    Node = osm.get('node', [])
    if not isinstance(Node, list): Node = [Node]
    original_ids, xy = [], []
    orig2small, small2orig = {}, {}

    for node in Node:
        try:
            nid = int(node["@id"])
            if nid not in road_node_ids: continue
            lat, lon = float(node["@lat"]), float(node["@lon"])
            idx = len(original_ids)
            original_ids.append(nid)
            xy.append((lat, lon))
            orig2small[nid] = idx
            small2orig[idx] = nid
        except:
            continue

    N = len(original_ids)
    adj_list = defaultdict(list)
    for nodes in ways:
        for i in range(len(nodes) - 1):
            u, v = nodes[i], nodes[i + 1]
            if u in orig2small and v in orig2small:
                a, b = orig2small[u], orig2small[v]
                adj_list[a].append((b, 1))
                adj_list[b].append((a, 1))

    joblib.dump(adj_list, f"{cache_dir}/graph.pkl")
    joblib.dump(xy, f"{cache_dir}/xy.pkl")
    joblib.dump(original_ids, f"{cache_dir}/original_ids.pkl")

tree = KDTree(xy)

def dijkstra(src, dst, adj):
    dist = {i: float('inf') for i in adj}
    prev = {i: None for i in adj}
    dist[src] = 0
    pq = [(0, src)]
    visited = set()
    while pq:
        d, u = heapq.heappop(pq)
        if u == dst:
            break
        if u in visited:
            continue
        visited.add(u)
        for v, w in adj[u]:
            alt = d + w
            if alt < dist[v]:
                dist[v], prev[v] = alt, u
                heapq.heappush(pq, (alt, v))
    return dist, prev

def build_path(dst, prev):
    path = []
    while dst is not None:
        path.append(dst)
        dst = prev[dst]
    return list(reversed(path))

def draw_all_routes(base_path, alternatives, filename="CombinedMap.html"):
    fmap = folium.Map(location=xy[base_path[0]], zoom_start=15)
    colors = ["green", "red", "blue", "purple", "orange"]
    folium.PolyLine([xy[i] for i in base_path], color=colors[0], weight=6, tooltip="Shortest route").add_to(fmap)
    for i, path in enumerate(alternatives):
        folium.PolyLine([xy[j] for j in path], color=colors[i+1], weight=5, tooltip=f"Alt Route {i+1}").add_to(fmap)
    fmap.save("static/" + filename)

def build_alternative_routes(src, dst, max_routes=4):
    dist, prev = dijkstra(src, dst, adj_list)
    if dist[dst] == float('inf'):
        return [], []
    base_path = build_path(dst, prev)
    central_nodes = sorted(base_path[1:-1], key=lambda x: len(adj_list[x]), reverse=True)
    alt_paths = []
    attempts = 0
    for skip in central_nodes:
        modified_adj = {k: list(v) for k, v in adj_list.items()}
        for neighbor in list(modified_adj[skip]):
            modified_adj[neighbor[0]] = [e for e in modified_adj[neighbor[0]] if e[0] != skip]
        modified_adj[skip] = []
        dist_alt, prev_alt = dijkstra(src, dst, modified_adj)
        if dist_alt[dst] < float('inf'):
            path = build_path(dst, prev_alt)
            if path not in alt_paths and len(set(base_path) & set(path)) < 0.8 * len(base_path):
                alt_paths.append(path)
        attempts += 1
        if len(alt_paths) >= max_routes or attempts >= len(base_path):
            break
    return base_path, alt_paths

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/hyperlink.html", methods=["GET", "POST"])
def demo():
    if request.method == "POST":
        src = request.form.get("pickup")
        dst = request.form.get("drop")
        action = request.form.get("action")
        try:
            geo = Nominatim(user_agent="quickpath")
            src_loc = geo.geocode(src)
            dst_loc = geo.geocode(dst)
            if not src_loc or not dst_loc:
                return render_template("hyperlink.html", message="❌ Location not found!")

            src_idx = tree.query((src_loc.latitude, src_loc.longitude))[1]
            dst_idx = tree.query((dst_loc.latitude, dst_loc.longitude))[1]

            if action == "shortest":
                dist, prev = dijkstra(src_idx, dst_idx, adj_list)
                if dist[dst_idx] == float('inf'):
                    return render_template("hyperlink.html", message="⚠ No route found!")
                path = build_path(dst_idx, prev)
                draw_all_routes(path, [])
                return redirect(url_for("show_alternatives"))

            elif action == "alternatives":
                base_path, alternatives = build_alternative_routes(src_idx, dst_idx)
                if not base_path:
                    return render_template("hyperlink.html", message="⚠ No route found!")
                draw_all_routes(base_path, alternatives)
                return redirect(url_for("show_alternatives"))

        except Exception as e:
            return render_template("hyperlink.html", message=f"Error: {e}")

    return render_template("hyperlink.html")

@app.route("/alternatives")
def show_alternatives():
    return render_template("combined_map.html")

if __name__ == "__main__":
    app.run(debug=True)
