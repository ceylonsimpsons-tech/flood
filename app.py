#!/usr/bin/env python3
"""
app.py - Generates index.html with EMBEDDED GeoJSON.

Usage:
  1. python app.py
  2. Upload 'index.html' to GitHub.
  3. Delete 'vercel.json' (it is not needed).
"""

import sys
import json
from pathlib import Path
import webbrowser
import http.server
import socketserver

# Config
GEOJSON_FILE = "kelani.geojson"
INDEX_FILE = "index.html"

def get_geojson_content():
    """Reads GeoJSON and returns it as a string to embed."""
    path = Path(GEOJSON_FILE)
    if not path.exists():
        print(f"❌ [ERROR] '{GEOJSON_FILE}' not found.")
        print("   Make sure the file is in this folder.")
        sys.exit(1)
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return json.dumps(data)
    except Exception as e:
        print(f"❌ [ERROR] Could not read JSON: {e}")
        sys.exit(1)

def write_index_html(json_data):
    """Writes the HTML file with the data inside it."""
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Kelani Flood Map</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <style>
    body, html, #map {{ height: 100%; margin: 0; padding: 0; background: #111; }}
  </style>
</head>
<body>
  <div id="map"></div>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    // 1. Setup Map
    const map = L.map('map');
    
    // 2. Satellite Layer
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
        attribution: 'Esri',
        maxZoom: 19
    }}).addTo(map);

    // 3. YOUR DATA (Embedded)
    const geoJsonData = {json_data};

    // 4. Add Polygon
    const layer = L.geoJSON(geoJsonData, {{
        style: {{
            color: '#00ccff',      // Bright Cyan
            weight: 3,
            fillColor: '#00ccff',
            fillOpacity: 0.3
        }},
        onEachFeature: function(feature, layer) {{
            if (feature.properties) {{
                let p = '<div style="color:black; font-family:sans-serif;">';
                for (let k in feature.properties) {{
                    p += '<b>' + k + ':</b> ' + feature.properties[k] + '<br>';
                }}
                p += '</div>';
                layer.bindPopup(p);
            }}
        }}
    }}).addTo(map);

    // 5. Auto Zoom
    map.fitBounds(layer.getBounds());
  </script>
</body>
</html>
"""
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(html)

def serve_local():
    port = 8000
    handler = http.server.SimpleHTTPRequestHandler
    print(f"\n🌍 Preview at http://localhost:{port}")
    print("   (Press Ctrl+C to stop)")
    with socketserver.TCPServer(("", port), handler) as httpd:
        webbrowser.open(f"http://localhost:{port}")
        try: httpd.serve_forever()
        except KeyboardInterrupt: pass

def main():
    print("--- 🗺️  Map Generator ---")
    
    # 1. Read Data
    data = get_geojson_content()
    
    # 2. Write HTML
    write_index_html(data)
    print(f"✅ Generated '{INDEX_FILE}' with embedded data.")

    # 3. Check for vercel.json (and warn user)
    if Path("vercel.json").exists():
        print("\n⚠️  WARNING: Found 'vercel.json'.")
        print("   Please DELETE this file. It is causing your Vercel errors.")

    if "--serve" in sys.argv:
        serve_local()
    else:
        print("\n🚀 NEXT STEPS:")
        print(f"1. Delete 'vercel.json' if it exists.")
        print(f"2. git add {INDEX_FILE}")
        print(f"3. git commit -m 'Update map'")
        print("4. git push")

if __name__ == "__main__":
    main()
