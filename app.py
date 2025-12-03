#!/usr/bin/env python3
"""
app.py - generate index.html + vercel.json with QGIS-like layer controls.

Files expected in same folder:
 - sentinel_2025-11-30.tif
 - kelani.geojson

Usage:
  python app.py          # generate index.html + vercel.json
  python app.py --serve  # generate files then start a local server
"""

import sys
import json
from pathlib import Path

SAFE_TIF = "sentinel_2025-11-30.tif"
GEOJSON = "kelani.geojson"
INDEX = "index.html"
VERCEL = "vercel.json"

cwd = Path.cwd()

def list_files():
    return sorted([p.name for p in cwd.iterdir()])

def check_files():
    tif_exists = (cwd / SAFE_TIF).exists()
    geo_exists = (cwd / GEOJSON).exists()
    return tif_exists, geo_exists

def write_index_html():
    index_html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Flood Map (QGIS Style)</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <style>
    html, body, #map {{ height:100%; margin:0; padding:0; }} 
    #map {{ width:100%; height:100vh; background: #202020; }}
  </style>
</head>
<body>
  <div id="map"></div>
  
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script src="https://unpkg.com/georaster@1.6.0/dist/georaster.browserify.min.js"></script>
  <script src="https://unpkg.com/georaster-layer-for-leaflet@3.10.0/dist/georaster-layer-for-leaflet.min.js"></script>
  
  <script>
  document.addEventListener("DOMContentLoaded", async function() {{
    // 1. Define Base Maps
    const osm = L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
        maxZoom: 19, 
        attribution: '&copy; OpenStreetMap'
    }});

    const satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
        attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
    }});

    // Initialize Map
    const map = L.map('map', {{
        center: [7.2, 80.6], 
        zoom: 9,
        layers: [satellite] 
    }});

    // 2. Setup Layer Groups
    const baseMaps = {{
        "Satellite Map": satellite,
        "Standard Map": osm
    }};
    
    const overlayMaps = {{}};
    const layerControl = L.control.layers(baseMaps, overlayMaps, {{ collapsed: false }}).addTo(map);

    const tifUrl = '{SAFE_TIF}';
    const geojsonUrl = '{GEOJSON}';

    // --- Helper to load TIFF ---
    async function loadGeoTIFF(url) {{
      const resp = await fetch(url);
      if (!resp.ok) throw new Error('Failed to fetch ' + url);
      const arrayBuffer = await resp.arrayBuffer();
      
      // FIX: Access parseGeoraster from the window object explicitly
      if (typeof window.parseGeoraster !== 'function') {{
         console.error("GeoRaster library not loaded correctly");
         throw new Error("parseGeoraster is missing");
      }}
      
      return await window.parseGeoraster(arrayBuffer);
    }}

    // 3. Load Sentinel TIFF (Raster)
    try {{
      const georaster = await loadGeoTIFF(tifUrl);
      
      const rasterLayer = new GeoRasterLayer({{
        georaster: georaster,
        opacity: 1.0,
        resolution: 256,
        pixelValuesToColorFn: function(pixelValues) {{
          if (!pixelValues) return null;
          
          const scale = (value) => {{
            if (value <= 1.5 && value >= 0) return Math.round(value * 255); 
            // 16-bit scaling
            let scaled = value / 15; 
            if (scaled > 255) scaled = 255;
            if (scaled < 0) scaled = 0;
            return Math.round(scaled);
          }};

          if (pixelValues.length >= 3) {{
            const r = scale(pixelValues[0]);
            const g = scale(pixelValues[1]);
            const b = scale(pixelValues[2]);
            if (r === 0 && g === 0 && b === 0) return null; 
            return 'rgba(' + r + ',' + g + ',' + b + ', 1)';
          }}
          
          const gray = scale(pixelValues[0]);
          if (gray === 0) return null;
          return 'rgba(' + gray + ',' + gray + ',' + gray + ', 1)';
        }}
      }});
      
      rasterLayer.addTo(map);
      layerControl.addOverlay(rasterLayer, "Sentinel Imagery");
      map.fitBounds(rasterLayer.getBounds());
      
    }} catch(e) {{
      console.warn('Raster load skipped or failed:', e);
    }}

    // 4. Load Kelani GeoJSON
    try {{
      const r = await fetch(geojsonUrl);
      if (r.ok) {{
        const gj = await r.json();
        const floodLayer = L.geoJSON(gj, {{
          style: {{
            color: '#00BFFF',       
            weight: 2,
            fillColor: '#00BFFF',   
            fillOpacity: 0.3        
          }},
          onEachFeature: function(feature, layer) {{
            const props = feature.properties || {{}};
            let popup = '<h3>Flood Area</h3>';
            for (let k in props) popup += '<b>' + k + '</b>: ' + props[k] + '<br>';
            layer.bindPopup(popup);
          }}
        }});

        floodLayer.addTo(map);
        layerControl.addOverlay(floodLayer, "Flooded Areas");
        floodLayer.bringToFront();
      }}
    }} catch(e) {{
      console.warn('GeoJSON load error:', e);
    }}

  }});
  </script>
</body>
</html>
"""
    with open(INDEX, "w", encoding="utf-8") as f:
        f.write(index_html)

def write_vercel_json():
    vercel_json = {
        "version": 2,
        "builds": [ { "src": INDEX, "use": "@vercel/static" } ],
        "routes": [ { "src": "/(.*)", "dest": "/" + INDEX } ]
    }
    with open(VERCEL, "w", encoding="utf-8") as f:
        json.dump(vercel_json, f, indent=2)

def serve_local(port=8000):
    import http.server
    import socketserver
    import webbrowser
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        url = f"http://localhost:{port}/"
        print(f"Serving current folder at {url}  (Press Ctrl+C to stop)")
        try: webbrowser.open(url)
        except Exception: pass
        try: httpd.serve_forever()
        except KeyboardInterrupt: print("\nServer stopped.")

def main():
    tif_exists, geo_exists = check_files()
    print("--- Flood Map Generator ---")
    if not tif_exists: print(f"[MISSING] {SAFE_TIF}")
    else: print(f"[OK] {SAFE_TIF}")
    if not geo_exists: print(f"[MISSING] {GEOJSON}")
    else: print(f"[OK] {GEOJSON}")

    write_index_html()
    write_vercel_json()
    print(f"\nGenerated '{INDEX}'.")

    if "--serve" in sys.argv or "-s" in sys.argv:
        serve_local(port=8000)
    else:
        print("To preview, run: python app.py --serve")

if __name__ == "__main__":
    main()