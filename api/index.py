"""Vercel entry point: the same request handling as server.py, one function per request."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from http.server import BaseHTTPRequestHandler  # noqa: E402

from server import MAX_BODY_BYTES, SECURITY_HEADERS, cache_control, process_api_request  # noqa: E402
import json  # noqa: E402


class handler(BaseHTTPRequestHandler):  # noqa: N801 - the name Vercel looks for
    def _send(self, status: int, payload: dict) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", cache_control(self.command, self.path, status))
        self.send_header("Content-Length", str(len(raw)))
        for name, value in SECURITY_HEADERS.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        self._send(*process_api_request("GET", self.path))

    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send(400, {"error": "Invalid Content-Length"})
            return
        if length < 0 or length > MAX_BODY_BYTES:
            self._send(413, {"error": f"Body larger than {MAX_BODY_BYTES} bytes"})
            return
        self._send(*process_api_request("POST", self.path, self.rfile.read(length) if length else b""))

    def log_message(self, format: str, *args) -> None:
        pass
