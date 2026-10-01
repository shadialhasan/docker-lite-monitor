# -*- coding: utf-8 -*-
"""
Automated Unit and Integration Tests for Docker Lite Monitor
Author: Eng. MHD. Shadi AL-Hasan <mhd.shadi.alhasan@gmail.com>
"""

import json
import socket
import threading
import urllib.request
import urllib.error
import subprocess
from unittest.mock import patch

import pytest
from monitor import (
    get_containers,
    compute_container_stats,
    render_html_dashboard,
    create_server,
    build_parser,
    MOCK_CONTAINERS
)


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


class TestDockerLiteMonitor:
    def test_mock_containers_structure(self):
        containers = get_containers(force_mock=True)
        assert isinstance(containers, list)
        assert len(containers) >= 1
        for c in containers:
            assert "ID" in c
            assert "Names" in c
            assert "Image" in c
            assert "Status" in c

    def test_get_containers_docker_cli_success(self):
        sample_docker_out = (
            '{"ID":"112233445566","Names":"web_proxy","Image":"nginx:latest","Status":"Up 3 hours","Ports":"80/tcp"}\n'
            '{"ID":"665544332211","Names":"db_cache","Image":"redis:alpine","Status":"Exited (0)","Ports":""}\n'
        ).encode('utf-8')

        with patch("subprocess.check_output", return_value=sample_docker_out):
            containers = get_containers(force_mock=False)
            assert len(containers) == 2
            assert containers[0]["Names"] == "web_proxy"
            assert containers[1]["Names"] == "db_cache"

    def test_get_containers_cli_failure_fallback(self):
        with patch("subprocess.check_output", side_effect=FileNotFoundError("docker not found")):
            containers = get_containers(force_mock=False)
            assert containers == MOCK_CONTAINERS

    def test_compute_container_stats(self):
        sample = [
            {"Status": "Up 2 hours"},
            {"Status": "Up 10 minutes"},
            {"Status": "Exited (137) 1 hour ago"},
            {"Status": "Created"}
        ]
        stats = compute_container_stats(sample)
        assert stats["total"] == 4
        assert stats["running"] == 2
        assert stats["stopped"] == 2

    def test_render_html_dashboard(self):
        html = render_html_dashboard(MOCK_CONTAINERS, refresh_interval=15, is_mock=True)
        assert "<!DOCTYPE html>" in html
        assert "Docker Lite Monitor" in html
        assert "Eng. MHD. Shadi AL-Hasan" in html
        assert 'content="15"' in html
        assert "nginx_edge_proxy" in html

    def test_cli_parser_defaults_and_custom(self, monkeypatch):
        monkeypatch.delenv("MONITOR_PORT", raising=False)
        monkeypatch.delenv("MONITOR_HOST", raising=False)
        parser = build_parser()
        args = parser.parse_args(["--port", "8081", "--host", "127.0.0.1", "--mock", "--refresh", "20"])
        assert args.port == 8081
        assert args.host == "127.0.0.1"
        assert args.mock is True
        assert args.refresh == 20

    def test_http_server_endpoints(self):
        port = get_free_port()
        server = create_server("127.0.0.1", port, force_mock=True, refresh_interval=5)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

        base_url = f"http://127.0.0.1:{port}"

        try:
            # 1. Test root dashboard
            with urllib.request.urlopen(f"{base_url}/") as response:
                assert response.status == 200
                content_type = response.headers.get("Content-Type")
                assert "text/html" in content_type
                body = response.read().decode("utf-8")
                assert "Docker Lite Monitor" in body
                assert "Eng. MHD. Shadi AL-Hasan" in body

            # 2. Test /health endpoint
            with urllib.request.urlopen(f"{base_url}/health") as response:
                assert response.status == 200
                data = json.loads(response.read().decode("utf-8"))
                assert data["status"] == "UP"
                assert data["service"] == "docker-lite-monitor"
                assert "author" in data
                assert data["containers"]["total"] > 0

            # 3. Test /api/containers endpoint
            with urllib.request.urlopen(f"{base_url}/api/containers") as response:
                assert response.status == 200
                containers = json.loads(response.read().decode("utf-8"))
                assert isinstance(containers, list)
                assert len(containers) > 0

            # 4. Test 404 handler
            try:
                urllib.request.urlopen(f"{base_url}/unknown-route")
            except urllib.error.HTTPError as err:
                assert err.code == 404
        finally:
            server.shutdown()
            server.server_close()
