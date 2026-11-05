"""
Moroccan Law AI & Official Gazette (Jarida Rasmiya) Redline Engine — Full-Stack Server
Serves:
- REST API (/api/health, /api/query, /api/laws, /api/law, /api/article, /api/catalog, /api/bo-issues, /api/bo-diff, /api/audit-contract)
- Usage counters in SQLite (MIZAN_STATS_DB, default data/legal_audit.db). Questions themselves are never stored.
- The React front end ("Mizan") built into web/dist (run `npm run build` inside web/)
"""

import json
import mimetypes
import os
import sqlite3
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional
from urllib.parse import parse_qs, unquote, urlparse

from src.bo_diff_engine import BulletinOfficielDiffEngine
from src.contract_auditor import MoroccanContractAuditor
from src.legal_rag import MoroccanLegalRAG, _article_label

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
STATIC_DIR = os.path.join(BASE_DIR, "web", "dist")
DB_PATH = os.environ.get("MIZAN_STATS_DB") or os.path.join(DATA_DIR, "legal_audit.db")

MAX_BODY_BYTES = 1_000_000
MAX_QUESTION_CHARS = 2_000
STATS_TIMEOUT_SECONDS = 0.25
# The law text only changes when the corpus is rebuilt, so shared caches may keep these for a day.
CACHEABLE_ROUTES = ("/api/laws", "/api/law", "/api/article", "/api/catalog", "/api/bo-issues")
CACHE_HEADER = "public, max-age=300, s-maxage=86400, stale-while-revalidate=604800"


def cache_control(method: str, path: str, status: int) -> str:
    route = urlparse(path).path
    return CACHE_HEADER if method == "GET" and status == 200 and route in CACHEABLE_ROUTES else "no-store"

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


@contextmanager
def _stats_connection():
    """
    Counters live on local disk, or in the temp directory where that is read-only. They are a convenience,
    so a slow or locked database gives up quickly rather than delaying someone's answer.
    """
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH, timeout=STATS_TIMEOUT_SECONDS)
        conn.execute("CREATE TABLE IF NOT EXISTS _probe (x INTEGER)")
    except (OSError, sqlite3.Error):
        conn = sqlite3.connect(os.path.join(tempfile.gettempdir(), "mizan_stats.db"), timeout=STATS_TIMEOUT_SECONDS)
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def _counters_enabled() -> bool:
    # On serverless hosts each instance has its own temp disk, so counts there would mean nothing.
    return not os.environ.get("VERCEL")


def init_db() -> None:
    with _stats_connection() as conn:
        # A legal question can reveal a private situation, so only its shape is counted, never its words
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS consultation_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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


def log_consultation(lang: str, domain: str, verified: bool, count: int) -> None:
    if not _counters_enabled():
        return
    try:
        init_db()
        with _stats_connection() as conn:
            conn.execute(
                "INSERT INTO consultation_stats (lang, domain, verified, citations_count, created_at) VALUES (?, ?, ?, ?, ?)",
                (lang, domain, 1 if verified else 0, count, datetime.now(timezone.utc).isoformat()),
            )
    except (OSError, sqlite3.Error) as exc:
        print(f"[stats] not counted: {exc}", file=sys.stderr)


def log_contract_audit(status: str, risk_score: int, violations_count: int) -> None:
    if not _counters_enabled():
        return
    try:
        init_db()
        with _stats_connection() as conn:
            conn.execute(
                "INSERT INTO contract_audits (status, risk_score, violations_count, created_at) VALUES (?, ?, ?, ?)",
                (status, risk_score, violations_count, datetime.now(timezone.utc).isoformat()),
            )
    except (OSError, sqlite3.Error) as exc:
        print(f"[stats] not counted: {exc}", file=sys.stderr)


def get_audit_stats() -> dict:
    if not _counters_enabled():
        return {"consultations_logged": 0, "contract_audits_logged": 0}
    try:
        init_db()
        with _stats_connection() as conn:
            c_count = conn.execute("SELECT COUNT(*) FROM consultation_stats").fetchone()[0]
            a_count = conn.execute("SELECT COUNT(*) FROM contract_audits").fetchone()[0]
    except (OSError, sqlite3.Error):
        return {"consultations_logged": 0, "contract_audits_logged": 0}
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
            "retrieval_engine": rag_engine.retrieval_engine,
            "corpus_articles_count": rag_engine.article_count,
            "corpus_laws_count": len(rag_engine.corpus.laws),
            "catalog_documents_count": int(rag_engine.corpus.meta.get("catalog_documents", 0)),
            "corpus_built_at": rag_engine.corpus.meta.get("built_at", ""),
            "bo_issues_count": len(bo_engine.list_bo_issues()),
            **stats,
        }

    if route == "/api/bo-issues" and method == "GET":
        audience = qs.get("audience", [None])[0]
        issues = bo_engine.list_bo_issues(audience=audience)
        return 200, {"count": len(issues), "issues": issues}

    if route == "/api/query" and method == "POST":
        payload = _json_body(body_bytes)
        query = str(payload.get("query", "")).strip()[:MAX_QUESTION_CHARS]
        if not query:
            raise BadRequest("Ask a question: the query field is empty")
        lang = str(payload.get("lang", "ar")).strip()
        res = rag_engine.answer_query(query, lang=lang)
        log_consultation(
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

    if route == "/api/laws" and method == "GET":
        laws = sorted(rag_engine.corpus.laws.values(), key=lambda law: (law["domain"], law["title_fr"]))
        return 200, {"count": len(laws), "built_at": rag_engine.corpus.meta.get("built_at", ""), "laws": laws}

    if route == "/api/article" and method == "GET":
        law = qs.get("law", [""])[0]
        number = qs.get("number", [""])[0]
        if law not in rag_engine.corpus.laws:
            return 404, {"error": "Unknown law"}
        citation = rag_engine.citation(law, number)
        if citation is None:
            return 404, {"error": "No such article in this law"}
        return 200, citation

    if route == "/api/law" and method == "GET":
        law = qs.get("law", [""])[0]
        if law not in rag_engine.corpus.laws:
            return 404, {"error": "Unknown law"}
        lang = qs.get("lang", ["ar"])[0]
        rows = rag_engine.corpus.law_articles(law, "fr" if lang == "fr" else "ar")
        return 200, {
            "law": rag_engine.corpus.laws[law],
            "articles": [
                {
                    "number": r["number"],
                    "label": _article_label(r["kind"], r["number"])[1 if lang == "fr" else 0],
                    "section": r["section"],
                    "page": r["page_from"],
                    "text": r["text"],
                }
                for r in rows
            ],
        }

    if route == "/api/catalog" and method == "GET":
        query = qs.get("q", [""])[0].strip()[:MAX_QUESTION_CHARS]
        lang = qs.get("lang", [None])[0]
        documents = rag_engine.corpus.search_catalog(query, lang=lang if lang in ("ar", "fr") else None)
        return 200, {"count": len(documents), "documents": documents}

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
        self.send_header("Cache-Control", cache_control(self.command, self.path, status_code))
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
    host = os.environ.get("HOST", "127.0.0.1")
    server = ThreadingHTTPServer((host, port), MoroccanLawHTTPRequestHandler)
    print(f"Mizan (moroccan-law-ai) running on http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Mizan] Server stopped cleanly by user.")
    finally:
        server.server_close()


if __name__ == "__main__":
    port_num = int(os.environ.get("PORT", "8090"))
    run_server(port_num)
