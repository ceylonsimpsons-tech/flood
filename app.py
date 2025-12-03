#!/usr/bin/env python3
"""
app.py - GeoJSON Map Generator with Debugging

Files expected:
 - kelani.geojson

Usage:
  python app.py --serve
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

def write_index_html():
    html_content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Kelani Debug Map</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <style>
    body, html {{ margin:0; padding:0; height:100%; }}
    #map {{ width:100%; height:100%; background: #222; }}
    #status {{
        position: absolute; top: 10px; left: 50px; z-index: 1000;
        background: white; padding: 10px; border: 2px solid red;
        display: none; font-family: sans-serif; max-width: 300px;
    }}
  </style>
</head>
<body>
  <div id="status"></div>
  <div id="map"></div>
  
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  
  <script>
  function showDeepError(msg) {{
      const el = document.getElementById('status');
      el.style.display = 'block';
      el.innerHTML += "⚠️ <b>Error:</b> " + msg + "<br>";
      console.error(msg);
  }}

  document.addEventListener("DOMContentLoaded", async function() {{
    const map = L.map('map').setView([6.9, 79.9], 10);

    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
        attribution: 'Esri'
    }}).addTo(map);

    const url = '{GEOJSON_FILE}';
    console.log("Attempting to fetch:", url);

    try {{
      const resp = await fetch(url);
      
      if (!resp.ok) {{
          throw new Error(`HTTP Error ${{resp.status}} (File not found?)`);
      }}

      const data = await resp.json();
      console.log("GeoJSON loaded:", data);

      if (!data.features || data.features.length === 0) {{
          showDeepError("File loaded, but it has 0 features (empty).");
          return;
      }}

      // --- CRITICAL CHECK: COORDINATE SYSTEM ---
      // Leaflet requires WGS84 (Lat/Lon). 
      // If numbers are huge (like 300,000), it's in Meters (UTM/SLD99).
      try {{
          // Check the first coordinate of the first feature
          let firstCoord = null;
          const geom = data.features[0].geometry;
          
          if (geom.type === 'Point') firstCoord = geom.coordinates[0];
          else if (geom.type === 'LineString') firstCoord = geom.coordinates[0][0];
          else if (geom.type === 'Polygon') firstCoord = geom.coordinates[0][0][0];
          else if (geom.type === 'MultiPolygon') firstCoord = geom.coordinates[0][0][0][0];

          if (firstCoord && firstCoord > 180) {{
             showDeepError("<b>Wrong Projection Detected!</b><br>Coordinates are > 180.<br>Your GeoJSON is likely in Meters (EPSG:5235 or UTM).<br>Export it from QGIS as <b>EPSG:4326 (WGS 84)</b>.");
          }}
      }} catch(e) {{ console.warn("Could not validate coords", e); }}
      // ------------------------------------------

      const layer = L.geoJSON(data, {{
        style: {{ color: '#00ffff', weight: 3 }}
      }}).addTo(map);

      map.fitBounds(layer.getBounds());

    }} catch (err) {{
      showDeepError(err.message);
    }}
  }});
  </script>
</body>
</html>
"""
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)

def main():
    write_index_html()
    # Create a dummy vercel.json just in case
    with open(VERCEL_FILE, "w") as f: f.write('{}') 
    
    # Server logic
    port = 8000
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        url = f"http://localhost:{port}/"
        print(f"Serving at {url} ... check your browser.")
        webbrowser.open(url)
        try: httpd.serve_forever()
        except KeyboardInterrupt: pass

if __name__ == "__main__":
    main()
