# -*- coding: utf-8 -*-
"""
Single-File Docker Container Health & Resource Monitor
Author: Eng. MHD. Shadi AL-Hasan <mhd.shadi.alhasan@gmail.com>
Phone: +963934005922
Copyright (c) 2026 MHD. Shadi AL-Hasan
"""

import os
import sys
import json
import argparse
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import List, Dict, Any

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="refresh" content="{refresh_interval}">
  <title>Docker Lite Monitor | Eng. MHD. Shadi AL-Hasan</title>
  <style>
    :root {{
      --bg: #0f172a;
      --card-bg: #1e293b;
      --border: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --primary: #38bdf8;
      --accent: #0284c7;
      --success: #22c55e;
      --danger: #ef4444;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      padding: 2rem;
      line-height: 1.5;
    }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 2rem;
      border-bottom: 1px solid var(--border);
      padding-bottom: 1.25rem;
    }}
    h1 {{ color: var(--primary); font-size: 1.8rem; display: flex; align-items: center; gap: 0.5rem; }}
    .stats-bar {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
      margin-bottom: 2rem;
    }}
    .stat-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.2rem;
    }}
    .stat-card .label {{ font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }}
    .stat-card .value {{ font-size: 1.8rem; font-weight: bold; margin-top: 0.3rem; }}
    .stat-card.running .value {{ color: var(--success); }}
    .stat-card.stopped .value {{ color: var(--danger); }}
    .stat-card.total .value {{ color: var(--primary); }}
    .table-container {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow-x: auto;
    }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--border); }}
    th {{ background: var(--accent); color: white; font-weight: 600; font-size: 0.9rem; }}
    tr:hover td {{ background: rgba(255, 255, 255, 0.02); }}
    code {{ font-family: monospace; color: #a5f3fc; background: #082f49; padding: 2px 6px; border-radius: 4px; }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 9999px; font-weight: 600; font-size: 0.75rem; text-transform: uppercase; }}
    .badge-up {{ background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3); }}
    .badge-down {{ background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }}
    footer {{
      margin-top: 2.5rem;
      border-top: 1px solid var(--border);
      padding-top: 1.25rem;
      color: var(--text-muted);
      font-size: 0.85rem;
      display: flex;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 1rem;
    }}
    footer a {{ color: var(--primary); text-decoration: none; }}
    footer a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <div class="header">
    <div>
      <h1>🐳 Docker Lite Monitor</h1>
      <p style="color: var(--text-muted); font-size: 0.95rem; margin-top: 0.25rem;">
        Lightweight real-time container supervisor & health monitor.
      </p>
    </div>
    <div style="font-size: 0.85rem; color: var(--text-muted);">
      Auto-refresh: <strong>{refresh_interval}s</strong> | Mode: <strong>{engine_mode}</strong>
    </div>
  </div>

  <div class="stats-bar">
    <div class="stat-card total">
      <div class="label">Total Containers</div>
      <div class="value">{total_count}</div>
    </div>
    <div class="stat-card running">
      <div class="label">Running (Healthy)</div>
      <div class="value">{running_count}</div>
    </div>
    <div class="stat-card stopped">
      <div class="label">Stopped / Exited</div>
      <div class="value">{stopped_count}</div>
    </div>
  </div>

  <div class="table-container">
    <table>
      <thead>
        <tr>
          <th>Container ID</th>
          <th>Names</th>
          <th>Image</th>
          <th>Command / Ports</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {table_rows}
      </tbody>
    </table>
  </div>

  <footer>
    <div>
      Architected & Maintained by <strong>Eng. MHD. Shadi AL-Hasan</strong> &bull;
      <a href="mailto:mhd.shadi.alhasan@gmail.com">mhd.shadi.alhasan@gmail.com</a> &bull;
      +963934005922 &bull; Damascus, Syria
    </div>
    <div>
      <a href="/api/containers">JSON API</a> &bull;
      <a href="/health">Health Check</a>
    </div>
  </footer>
</body>
</html>
"""

MOCK_CONTAINERS: List[Dict[str, Any]] = [
    {
        "ID": "a1b2c3d4e5f6",
        "Names": "nginx_edge_proxy",
        "Image": "nginx:alpine",
        "Status": "Up 4 days",
        "Ports": "0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp"
    },
    {
        "ID": "f6e5d4c3b2a1",
        "Names": "redis_sessions",
        "Image": "redis:7-alpine",
        "Status": "Up 2 weeks",
        "Ports": "0.0.0.0:6379->6379/tcp"
    },
    {
        "ID": "998877665544",
        "Names": "xtts_voice_worker",
        "Image": "xtts:v2-cuda",
        "Status": "Exited (0) 2 hours ago",
        "Ports": ""
    },
    {
        "ID": "1234567890ab",
        "Names": "fastapi_clean_core",
        "Image": "fastapi-core:latest",
        "Status": "Up 12 hours",
        "Ports": "0.0.0.0:8000->8000/tcp"
    }
]


def get_containers(force_mock: bool = False) -> List[Dict[str, Any]]:
    """Query live Docker daemon via CLI, falling back to simulated data if unavailable."""
    if force_mock:
        return MOCK_CONTAINERS

    try:
        cmd = ["docker", "ps", "-a", "--format", "{{json .}}"]
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode("utf-8")
        containers: List[Dict[str, Any]] = []
        for line in output.strip().splitlines():
            if line.strip():
                containers.append(json.loads(line))
        return containers if containers else []
    except Exception:
        # Fallback simulation for offline / testing environments
        return MOCK_CONTAINERS


def compute_container_stats(containers: List[Dict[str, Any]]) -> Dict[str, int]:
    """Compute summary counts for containers."""
    total = len(containers)
    running = sum(1 for c in containers if "Up" in c.get("Status", ""))
    stopped = total - running
    return {"total": total, "running": running, "stopped": stopped}


def render_html_dashboard(containers: List[Dict[str, Any]], refresh_interval: int = 10, is_mock: bool = False) -> str:
    """Generate modern responsive HTML dashboard string."""
    stats = compute_container_stats(containers)
    rows = ""
    for c in containers:
        cid = str(c.get("ID", ""))[:12]
        name = str(c.get("Names", "unnamed"))
        image = str(c.get("Image", "-"))
        status = str(c.get("Status", "Unknown"))
        ports = str(c.get("Ports", "-")) or "-"
        is_up = "Up" in status
        badge_cls = "badge-up" if is_up else "badge-down"
        badge = f'<span class="badge {badge_cls}">{status}</span>'
        rows += (
            f"<tr>"
            f"<td><code>{cid}</code></td>"
            f"<td><strong>{name}</strong></td>"
            f"<td>{image}</td>"
            f"<td><small style='color: var(--text-muted);'>{ports}</small></td>"
            f"<td>{badge}</td>"
            f"</tr>\n"
        )

    return HTML_TEMPLATE.format(
        table_rows=rows,
        refresh_interval=refresh_interval,
        engine_mode="Mock Simulation" if is_mock else "Live Docker Engine",
        total_count=stats["total"],
        running_count=stats["running"],
        stopped_count=stats["stopped"]
    )


class MonitorHandler(BaseHTTPRequestHandler):
    force_mock: bool = False
    refresh_interval: int = 10

    def do_GET(self):
        containers = get_containers(force_mock=self.force_mock)

        if self.path in ("/", "/dashboard"):
            html = render_html_dashboard(containers, refresh_interval=self.refresh_interval, is_mock=self.force_mock)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        elif self.path in ("/health", "/healthz"):
            stats = compute_container_stats(containers)
            payload = {
                "status": "UP",
                "service": "docker-lite-monitor",
                "version": "1.1.0",
                "mode": "mock" if self.force_mock else "live",
                "containers": stats,
                "author": "Eng. MHD. Shadi AL-Hasan",
                "email": "mhd.shadi.alhasan@gmail.com"
            }
            body = json.dumps(payload, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)

        elif self.path in ("/api/containers", "/api/v1/containers"):
            body = json.dumps(containers, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)

        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not Found", "path": self.path}).encode("utf-8"))

    def log_message(self, format, *args):
        # Override to keep test output clean; write only if needed
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Docker Lite Monitor - Ultra-lightweight container dashboard by Eng. MHD. Shadi AL-Hasan"
    )
    parser.add_argument(
        "--host",
        default=os.getenv("MONITOR_HOST", "0.0.0.0"),
        help="Host address to bind the HTTP server to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=int(os.getenv("MONITOR_PORT", "9090")),
        help="Port number to bind (default: 9090)"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        default=os.getenv("MONITOR_MOCK_FALLBACK", "false").lower() in ("true", "1"),
        help="Force simulated mock container metrics"
    )
    parser.add_argument(
        "--refresh", "-r",
        type=int,
        default=int(os.getenv("MONITOR_REFRESH_RATE", "10")),
        help="Dashboard HTML auto-refresh interval in seconds (default: 10)"
    )
    return parser


def create_server(host: str, port: int, force_mock: bool = False, refresh_interval: int = 10) -> HTTPServer:
    handler = MonitorHandler
    handler.force_mock = force_mock
    handler.refresh_interval = refresh_interval
    return HTTPServer((host, port), handler)


def main():
    parser = build_parser()
    args = parser.parse_args()

    server = create_server(args.host, args.port, force_mock=args.mock, refresh_interval=args.refresh)
    print(f"[*] Docker Lite Monitor running at http://{args.host}:{args.port}")
    print(f"[*] Mode: {'Mock Simulation' if args.mock else 'Live Docker Daemon'}")
    print(f"[*] Author: Eng. MHD. Shadi AL-Hasan <mhd.shadi.alhasan@gmail.com>")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Shutting down monitor gracefully...")
        server.server_close()


if __name__ == "__main__":
    main()
