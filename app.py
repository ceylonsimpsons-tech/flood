#!/usr/bin/env python3
"""
app.py - Generates a self-contained HTML map.

Changes:
1. Reads 'kelani.geojson' during generation.
2. Embeds the data directly into index.html (No more fetch errors!).
3. Checks if your coordinates are valid (Lat/Lon) automatically.
"""

import sys
import json
from pathlib import Path
import webbrowser
import http.server
import socketserver

GEOJSON_FILE = "kelani.geojson"
INDEX_FILE = "index.html"
VERCEL_FILE = "vercel.json"

def get_geojson_content():
    """Reads the GeoJSON file and returns it as a JSON string."""
    path = Path(GEOJSON_FILE)
    if not path.exists():
        print(f"[ERROR] Could not find {GEOJSON_FILE}")
        sys.exit(1)
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # --- PROJECTION CHECK ---
        # We check the first coordinate to see if it looks like meters (wrong) or lat/lon (correct).
        try:
            # Drill down to find the first coordinate number
            feature = data['features'][0]
            geom = feature['geometry']
            coords = geom['coordinates']
            
            # Unwrap nested arrays until we find a number
            while isinstance(coords, list) and len(coords) > 0 and isinstance(coords[0], list):
                coords = coords[0]
            
            first_val = coords[0] if isinstance(coords, list) and len(coords) > 0 else 0

            if first_val > 180:
                print("\n[WARNING] ⚠️  YOUR COORDINATES LOOK WRONG!")
                print(f"   Value found: {first_val}")
                print("   The map expects Latitude/Longitude (WGS84).")
                print("   If you see a blank map, re-export from QGIS as 'EPSG:4326'.\n")
        except Exception as e:
            pass # Skip check if structure is complex
            
        return json.dumps(data)
    except Exception as e:
        print(f"[ERROR] Invalid JSON in {GEOJSON_FILE}: {e}")
        sys.exit(1)

def write_index_html(geojson_string):
    html_content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Kelani Map</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <style>
    body, html, #map {{ height: 100%; margin: 0; padding: 0; background: #222; }}
  </style>
</head>
<body>
  <div id="map"></div>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    // 1. Initialize Map
    const map = L.map('map');

    // 2. Add Satellite Layer
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
        attribution: 'Esri'
    }}).addTo(map);

    // 3. Embed the GeoJSON Data directly
    const geoData = {geojson_string};

    // 4. Load Data to Map
    const layer = L.geoJSON(geoData, {{
        style: {{
            color: '#00BFFF', 
            weight: 2, 
            fillColor: '#00BFFF', 
            fillOpacity: 0.3
        }},
        onEachFeature: function(feature, layer) {{
            if (feature.properties) {{
                let popup = '<div style="font-family:sans-serif; color:black;">';
                for (let k in feature.properties) {{
                    popup += '<b>' + k + ':</b> ' + feature.properties[k] + '<br>';
                }}
                popup += '</div>';
                layer.bindPopup(popup);
            }}
        }}
    }}).addTo(map);

    // 5. Auto-zoom to fit the polygon
    map.fitBounds(layer.getBounds());
  </script>
</body>
</html>
"""
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)

def write_vercel_json():
    config = {
        "version": 2,
        "builds": [{ "src": INDEX_FILE, "use": "@vercel/static" }],
        "routes": [{ "src": "/(.*)", "dest": "/" + INDEX_FILE }]
    }
    with open(VERCEL_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

def main():
    print("--- Generating Map ---")
    
    # Get content
    json_str = get_geojson_content()
    
    # Write files
    write_index_html(json_str)
    write_vercel_json()
    
    print(f"[SUCCESS] {INDEX_FILE} generated with embedded data.")

    if "--serve" in sys.argv:
        port = 8000
        print(f"Opening http://localhost:{port} ...")
        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", port), handler) as httpd:
            webbrowser.open(f"http://localhost:{port}")
            try: httpd.serve_forever()
            except KeyboardInterrupt: pass

if __name__ == "__main__":
    main()
