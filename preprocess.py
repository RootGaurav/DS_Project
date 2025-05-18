import xmltodict
import joblib
import os
from scipy.spatial import KDTree

# Create cache directory if it doesn't exist
os.makedirs("cache", exist_ok=True)

# Load OSM XML
with open("Maps/map.osm", "rb") as f:
    osm = xmltodict.parse(f)["osm"]

# Road types we care about
road_vals = {
    'motorway', 'trunk', 'primary', 'secondary', 'tertiary',
    'residential', 'living_street', 'service', 'unclassified',
    'road', 'track', 'path'
}

# Extract valid ways (roads)
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

# Extract node coordinates and create mappings
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

# Build adjacency list
N = len(original_ids)
adj_list = {i: [] for i in range(N)}
for nodes in ways:
    for i in range(len(nodes) - 1):
        u, v = nodes[i], nodes[i + 1]
        if u in orig2small and v in orig2small:
            a, b = orig2small[u], orig2small[v]
            if b not in [x[0] for x in adj_list[a]]:
                adj_list[a].append((b, 1))
            if a not in [x[0] for x in adj_list[b]]:
                adj_list[b].append((a, 1))

# Save data
joblib.dump(adj_list, "cache/graph.pkl")
joblib.dump(xy, "cache/xy.pkl")
joblib.dump(KDTree(xy), "cache/tree.pkl")
joblib.dump(small2orig, "cache/small2orig.pkl")
joblib.dump(orig2small, "cache/orig2small.pkl")

print(f"✅ Preprocessing complete: {N} nodes, {sum(len(v) for v in adj_list.values()) // 2} edges")
