"""
Moroccan Law AI & Official Gazette (Jarida Rasmiya) Redline Engine — Full-Stack Server
Serves:
- REST API (/api/health, /api/query, /api/bo-issues, /api/bo-diff, /api/audit-contract)
- Persistent SQLite Audit & Consultation Store (data/legal_audit.db)
- The React front end ("Mizan") built into web/dist (run `npm run build` inside web/)
"""

import json
import mimetypes
import os
import sqlite3
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional
from urllib.parse import parse_qs, unquote, urlparse

from src.bo_diff_engine import BulletinOfficielDiffEngine
from src.contract_auditor import MoroccanContractAuditor
from src.legal_rag import MoroccanLegalRAG

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
STATIC_DIR = os.path.join(BASE_DIR, "web", "dist")
DB_PATH = os.path.join(DATA_DIR, "legal_audit.db")

MAX_BODY_BYTES = 1_000_000

mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("application/manifest+json", ".webmanifest")

# Everything the UI needs is served from this origin; nothing is loaded from third parties.
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        "font-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'"
    ),
}

rag_engine = MoroccanLegalRAG()
bo_engine = BulletinOfficielDiffEngine()
contract_auditor = MoroccanContractAuditor()


def init_db() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS consultations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                lang TEXT NOT NULL,
                domain TEXT NOT NULL,
                verified INTEGER NOT NULL,
                citations_count INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS contract_audits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                violations_count INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def log_consultation(query: str, lang: str, domain: str, verified: bool, count: int) -> None:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO consultations (query, lang, domain, verified, citations_count, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (query, lang, domain, 1 if verified else 0, count, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()


def log_contract_audit(status: str, risk_score: int, violations_count: int) -> None:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO contract_audits (status, risk_score, violations_count, created_at) VALUES (?, ?, ?, ?)",
            (status, risk_score, violations_count, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()


def get_audit_stats() -> dict:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        c_count = conn.execute("SELECT COUNT(*) FROM consultations").fetchone()[0]
        a_count = conn.execute("SELECT COUNT(*) FROM contract_audits").fetchone()[0]
    return {"consultations_logged": c_count, "contract_audits_logged": a_count}


class BadRequest(ValueError):
    """Raised when a request body is not a JSON object."""


def _json_body(body_bytes: bytes) -> dict:
    try:
        payload = json.loads(body_bytes.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BadRequest("Request body must be valid UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise BadRequest("Request body must be a JSON object")
    return payload


def process_api_request(method: str, path_str: str, body_bytes: bytes = b"") -> tuple[int, dict]:
    try:
        return _route_api_request(method, path_str, body_bytes)
    except BadRequest as exc:
        return 400, {"error": str(exc)}


def _route_api_request(method: str, path_str: str, body_bytes: bytes = b"") -> tuple[int, dict]:
    parsed = urlparse(path_str)
    route = parsed.path
    qs = parse_qs(parsed.query)

    if route == "/api/health" and method == "GET":
        stats = get_audit_stats()
        return 200, {
            "status": "ok",
            "app": "moroccan-law-ai",
            "retrieval_engine": "Hybrid Okapi BM25 + Trigram Vector RRF (k=60)",
            "corpus_articles_count": len(rag_engine.db),
            "bo_issues_count": len(bo_engine.list_bo_issues()),
            **stats,
        }

    if route == "/api/bo-issues" and method == "GET":
        audience = qs.get("audience", [None])[0]
        issues = bo_engine.list_bo_issues(audience=audience)
        return 200, {"count": len(issues), "issues": issues}

    if route == "/api/query" and method == "POST":
        payload = _json_body(body_bytes)
        query = str(payload.get("query", "")).strip() or "ما هي حقوق الأجير في حالة الطرد التعسفي؟"
        lang = str(payload.get("lang", "ar")).strip()
        res = rag_engine.answer_query(query, lang=lang)
        log_consultation(
            query=query,
            lang=lang,
            domain=res["domain"],
            verified=res["citation_verified"],
            count=len(res["verbatim_citations"]),
        )
        return 200, res

    if route == "/api/bo-diff" and method == "POST":
        payload = _json_body(body_bytes)
        old_text = str(payload.get("old_text", ""))
        new_text = str(payload.get("new_text", ""))
        article_ref = str(payload.get("article_ref", "Custom Statutory Comparison"))
        bo_issue = str(payload.get("bo_issue", "Custom BO"))
        diff = bo_engine.compute_article_redline_diff(
            old_text=old_text,
            new_text=new_text,
            article_ref=article_ref,
            bo_issue=bo_issue,
        )
        return 200, diff

    if route == "/api/audit-contract" and method == "POST":
        payload = _json_body(body_bytes)
        contract_text = str(payload.get("contract_text", ""))
        lang = str(payload.get("lang", "fr"))
        report = contract_auditor.audit_contract(contract_text, lang=lang)
        report["rules_checked"] = len(contract_auditor.COMPLIANCE_RULES)
        log_contract_audit(
            status=report["status"],
            risk_score=report["risk_score"],
            violations_count=report["violations_count"],
        )
        return 200, report

    return 404, {"error": f"Unknown API endpoint: {route}"}



def resolve_static(url_path: str) -> Optional[str]:
    """Maps a URL path to a file inside STATIC_DIR, or returns None.

    Rejects anything that resolves outside STATIC_DIR (``..``, encoded ``%2e%2e``, absolute paths,
    symlinks). Unknown extension-less paths fall back to index.html so client-side routes work.
    """
    root = os.path.realpath(STATIC_DIR)
    clean = unquote(urlparse(url_path).path)
    if "\x00" in clean:
        return None
    candidate = os.path.realpath(os.path.join(root, clean.lstrip("/\\")))
    if candidate != root and not candidate.startswith(root + os.sep):
        return None
    if os.path.isfile(candidate):
        return candidate
    if os.path.splitext(clean)[1] == "":
        index = os.path.join(root, "index.html")
        return index if os.path.isfile(index) else None
    return None


class MoroccanLawHTTPRequestHandler(BaseHTTPRequestHandler):
    server_version = "MizanServer/1.1"

    def _security_headers(self) -> None:
        for name, value in SECURITY_HEADERS.items():
            self.send_header(name, value)

    def _send_json(self, status_code: int, data: dict) -> None:
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self._security_headers()
        self.end_headers()
        self.wfile.write(raw)

    def _send_file(self, path: str) -> None:
        with open(path, "rb") as f:
            content = f.read()
        mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
        if mime.startswith("text/") or mime in ("application/javascript", "image/svg+xml"):
            mime += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", mime)
        # Vite emits content-hashed names under /assets, so those are safe to cache for a year.
        immutable = os.sep + "assets" + os.sep in path
        self.send_header(
            "Cache-Control", "public, max-age=31536000, immutable" if immutable else "no-cache"
        )
        self.send_header("Content-Length", str(len(content)))
        self._security_headers()
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:
        if self.path.startswith("/api/"):
            code, payload = process_api_request("GET", self.path)
            self._send_json(code, payload)
            return

        target = resolve_static(self.path)
        if target:
            self._send_file(target)
            return
        if not os.path.isfile(os.path.join(STATIC_DIR, "index.html")):
            self._send_json(
                503, {"error": "Front end not built. Run `npm ci && npm run build` inside web/."}
            )
            return
        self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        if not self.path.startswith("/api/"):
            self._send_json(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "Invalid Content-Length"})
            return
        if length < 0 or length > MAX_BODY_BYTES:
            self._send_json(413, {"error": f"Body larger than {MAX_BODY_BYTES} bytes"})
            return
        body = self.rfile.read(length) if length > 0 else b""
        code, payload = process_api_request("POST", self.path, body)
        self._send_json(code, payload)

    def log_message(self, format: str, *args) -> None:
        pass


def run_server(port: int = 8090) -> None:
    init_db()
    server = ThreadingHTTPServer(("127.0.0.1", port), MoroccanLawHTTPRequestHandler)
    print(f"Mizan (moroccan-law-ai) running on http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    port_num = int(os.environ.get("PORT", "8090"))
    run_server(port_num)
