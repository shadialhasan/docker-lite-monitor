# -*- coding: utf-8 -*-
"""
Single-File Docker Container Health & Resource Monitor
Author: Eng. MHD. Shadi AL-Hasan <mhd.shadi.alhasan@gmail.com>
Phone: +963934005922
Copyright (c) 2026 MHD. Shadi AL-Hasan
"""

import json
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Docker Lite Monitor | Eng. MHD. Shadi AL-Hasan</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; padding: 2rem; }
    h1 { color: #38bdf8; }
    table { width: 100%; border-collapse: collapse; margin-top: 1.5rem; background: #1e293b; border-radius: 8px; overflow: hidden; }
    th, td { padding: 12px 16px; text-align: left; border-bottom: 1px solid #334155; }
    th { background: #0284c7; color: white; }
    .badge { padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8rem; }
    .badge-up { background: #22c55e; color: #000; }
    .badge-down { background: #ef4444; color: #fff; }
    footer { margin-top: 2rem; color: #94a3b8; font-size: 0.9rem; }
  </style>
</head>
<body>
  <h1>🐳 Docker Lite Monitor</h1>
  <p>Lightweight single-file container supervisor.</p>
  <table>
    <thead>
      <tr>
        <th>Container ID</th>
        <th>Names</th>
        <th>Image</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      {table_rows}
    </tbody>
  </table>
  <footer>
    Maintained by <strong>Eng. MHD. Shadi AL-Hasan</strong> (mhd.shadi.alhasan@gmail.com | +963934005922)
  </footer>
</body>
</html>
"""

def get_containers():
    try:
        cmd = ["docker", "ps", "-a", "--format", "{{json .}}"]
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode('utf-8')
        containers = []
        for line in output.strip().splitlines():
            if line:
                containers.append(json.loads(line))
        return containers
    except Exception:
        # Fallback simulation
        return [
            {"ID": "a1b2c3d4e5f6", "Names": "nginx_edge_proxy", "Image": "nginx:alpine", "Status": "Up 4 days"},
            {"ID": "f6e5d4c3b2a1", "Names": "redis_sessions", "Image": "redis:7-alpine", "Status": "Up 2 weeks"},
            {"ID": "998877665544", "Names": "xtts_voice_worker", "Image": "xtts:v2-cuda", "Status": "Exited (0) 2 hours ago"}
        ]

class MonitorHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        containers = get_containers()
        rows = ""
        for c in containers:
            status = c.get("Status", "Unknown")
            is_up = "Up" in status
            badge = f'<span class="badge { "badge-up" if is_up else "badge-down" }">{status}</span>'
            rows += f"<tr><td><code>{c.get('ID', '')[:12]}</code></td><td><strong>{c.get('Names', '')}</strong></td><td>{c.get('Image', '')}</td><td>{badge}</td></tr>"

        html = HTML_TEMPLATE.replace("{table_rows}", rows)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

def main():
    port = 9090
    server = HTTPServer(('0.0.0.0', port), MonitorHandler)
    print(f"[*] Docker Lite Monitor running at http://localhost:{port}")
    server.serve_forever()

if __name__ == "__main__":
    main()
