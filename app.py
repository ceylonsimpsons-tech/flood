#!/usr/bin/env python3
"""
app.py - Simple GeoJSON Map Generator

Files expected in same folder:
 - kelani.geojson

Usage:
  python app.py          # generate index.html + vercel.json
  python app.py --serve  # generate files then start a local server
"""

import sys
import json
from pathlib import Path
import webbrowser
import http.server
import socketserver

# Configuration
GEOJSON_FILE = "kelani.geojson"
INDEX_FILE = "index.html"
VERCEL_FILE = "vercel.json"

cwd = Path.cwd()

def write_index_html():
    """Generates a clean, lightweight HTML file for GeoJSON viewing."""
    
    html_content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Kelani Flood Map</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <style>
    html, body, #map {{ height: 100%; margin: 0; padding: 0; }}
    #map {{ width: 100%; height: 100vh; background: #222; }}
    .leaflet-control-layers {{
        background: rgba(255, 255, 255, 0.9); 
        padding: 5px; 
        border-radius: 5px;
    }}
  </style>
</head>
<body>
  <div id="map"></div>
  
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  
  <script>
  document.addEventListener("DOMContentLoaded", async function() {{

    // --- 1. Base Maps ---
    const osm = L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
        maxZoom: 19, 
        attribution: '&copy; OpenStreetMap'
    }});

    const satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
        attribution: '&copy; Esri'
    }});

    // --- 2. Initialize Map ---
    const map = L.map('map', {{
        center: [6.9271, 79.8612], // Default: Colombo
        zoom: 10,
        layers: [satellite] // Default layer
    }});

    const baseMaps = {{ "Satellite": satellite, "Street Map": osm }};
    const overlayMaps = {{}};
    const layerControl = L.control.layers(baseMaps, overlayMaps, {{ collapsed: false }}).addTo(map);

    // --- 3. Load GeoJSON ---
    const geojsonUrl = '{GEOJSON_FILE}';

    try {{
      const response = await fetch(geojsonUrl);
      if (!response.ok) throw new Error("File not found");
      
      const data = await response.json();

      const geoJsonLayer = L.geoJSON(data, {{
        style: {{
          color: '#00BFFF',       // Deep Sky Blue outline
          weight: 2,
          fillColor: '#00BFFF',   // Blue fill
          fillOpacity: 0.4        // Semi-transparent
        }},
        onEachFeature: function(feature, layer) {{
          if (feature.properties) {{
            let popupContent = '<div style="font-family: sans-serif;"><h3>Feature Details</h3>';
            for (const [key, value] of Object.entries(feature.properties)) {{
                popupContent += `<b>${{key}}:</b> ${{value}}<br>`;
            }}
            popupContent += '</div>';
            layer.bindPopup(popupContent);
          }}
        }}
      }});

      geoJsonLayer.addTo(map);
      layerControl.addOverlay(geoJsonLayer, "Kelani River Data");
      
      // Auto-zoom to the data
      map.fitBounds(geoJsonLayer.getBounds());

    }} catch (err) {{
      console.error("Error loading GeoJSON:", err);
      alert("Could not load " + geojsonUrl + ". Check if the file exists.");
    }}

  }});
  </script>
</body>
</html>
"""
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)

def write_vercel_json():
    """Generates config for Vercel deployment."""
    config = {
        "version": 2,
        "builds": [{ "src": INDEX_FILE, "use": "@vercel/static" }],
        "routes": [{ "src": "/(.*)", "dest": "/" + INDEX_FILE }]
    }
    with open(VERCEL_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

def serve_local(port=8000):
    """Starts a simple local web server."""
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        url = f"http://localhost:{port}/"
        print(f"\n[SERVER] Serving at {url}")
        print("[SERVER] Press Ctrl+C to stop.")
        try:
            webbrowser.open(url)
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[SERVER] Stopped.")

def main():
    print("--- GeoJSON Map Generator ---")
    
    # Check for GeoJSON
    if (cwd / GEOJSON_FILE).exists():
        print(f"[OK] Found {GEOJSON_FILE}")
    else:
        print(f"[WARNING] {GEOJSON_FILE} not found. The map will be empty.")

    # Generate files
    write_index_html()
    write_vercel_json()
    print(f"[SUCCESS] Generated '{INDEX_FILE}' and '{VERCEL_FILE}'")

    # Handle arguments
    if "--serve" in sys.argv or "-s" in sys.argv:
        serve_local()
    else:
        print("\nTo view the map, run: python app.py --serve")

if __name__ == "__main__":
    main()
