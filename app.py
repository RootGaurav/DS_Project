from flask import Flask, render_template, request
import xmltodict, folium, heapq
from geopy.geocoders import Nominatim
from scipy.spatial import KDTree

app = Flask(__name__)

# Load and parse OSM
with open("Maps/smalldoon.osm", "rb") as f:
    osm = xmltodict.parse(f)["osm"]

road_vals = {'motorway', 'trunk', 'primary', 'secondary', 'tertiary',
             'residential', 'living_street', 'service', 'unclassified'}

ways = []
road_node_ids = set()
Way = osm.get('way', [])
if not isinstance(Way, list): Way = [Way]
for way in Way:
    tags = way.get('tag', [])
    if isinstance(tags, dict): tags = [tags]
    if not any(tag['@k'] == 'highway' and tag['@v'] in road_vals for tag in tags):
        continue
    nodes = [int(nd['@ref']) for nd in way.get('nd', [])]
    ways.append(nodes)
    road_node_ids.update(nodes)

# Node Parsing
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

Nnodes = len(original_ids)
tree = KDTree(xy)

# Build Adjacency List
def build_adj_list():
    adj = {i: [] for i in range(Nnodes)}
    for nodes in ways:
        for i in range(len(nodes) - 1):
            u, v = nodes[i], nodes[i + 1]
            if u in orig2small and v in orig2small:
                a, b = orig2small[u], orig2small[v]
                adj[a].append((b, 1))
                adj[b].append((a, 1))
    return adj

adj_list = build_adj_list()

# Dijkstra's Algorithm
def dijkstra(src, adj):
    dist = {i: float('inf') for i in adj}
    prev = {i: None for i in adj}
    dist[src] = 0
    pq = [(0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]: continue
        for v, w in adj[u]:
            alt = d + w
            if alt < dist[v]:
                dist[v], prev[v] = alt, u
                heapq.heappush(pq, (alt, v))
    return dist, prev

# Map Creator
def build_path_map(dst, prev):
    path = []
    while dst is not None:
        path.append(dst)
        dst = prev[dst]
    path.reverse()
    fmap = folium.Map(location=xy[path[0]], zoom_start=15)
    for idx in path:
        folium.CircleMarker(xy[idx], radius=4, color='blue', fill=True).add_to(fmap)
    folium.PolyLine([xy[idx] for idx in path], color='blue', weight=5).add_to(fmap)
    fmap.save("static/OutputMap.html")

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/hyperlink.html", methods=["GET", "POST"])
def demo():
    message = ""
    if request.method == "POST":
        src = request.form.get("pickup")
        dst = request.form.get("drop")
        try:
            geo = Nominatim(user_agent="quickpath")
            src_loc = geo.geocode(src)
            dst_loc = geo.geocode(dst)
            if not src_loc or not dst_loc:
                message = "❌ Location not found!"
            else:
                src_idx = tree.query((src_loc.latitude, src_loc.longitude))[1]
                dst_idx = tree.query((dst_loc.latitude, dst_loc.longitude))[1]
                dist, prev = dijkstra(src_idx, adj_list)
                if dist[dst_idx] == float('inf'):
                    message = "⚠ No route found!"
                else:
                    build_path_map(dst_idx, prev)
                    return render_template("output_map.html")
        except Exception as e:
            message = f"Error: {e}"
    return render_template("hyperlink.html", message=message)

if __name__ == "__main__":
    app.run(debug=True)
