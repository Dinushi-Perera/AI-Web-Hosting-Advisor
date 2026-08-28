import pytest
import shutil
import threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer

from app.services.k6_execution_service import _safe_environment,execute_generated_k6
from app.services.load_test_result_parser import parse_summary

@pytest.mark.skipif(shutil.which("k6") is None,reason="k6 is not installed in this test environment")
def test_managed_executor_returns_genuine_k6_summary():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200);self.end_headers();self.wfile.write(b"ok")
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(("127.0.0.1",0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    script=f"""/* AI Web Hosting Advisor server-generated scenario. */
import http from 'k6/http';
import {{ check }} from 'k6';
export const options = {{ vus: 1, iterations: 1, thresholds: {{ checks: ['rate>0.99'] }} }};
export default function () {{ http.get('http://127.0.0.1:{server.server_port}/'); check(true, {{ 'engine executes': value => value === true }}); }}
"""
    try:summary=execute_generated_k6(script,"test-plan")
    finally:server.shutdown();server.server_close()
    parsed=parse_summary(summary)

    assert summary["advisor_execution"]["engine"]=="k6"
    assert parsed["total_requests"]==1
    assert parsed["checks_passed"]==1
    assert parsed["checks_failed"]==0
    assert parsed["http_req_duration_p95_ms"] is not None
    assert parsed["http_req_failed_rate"] is not None

def test_managed_environment_keeps_uppercase_windows_systemroot(monkeypatch):
    monkeypatch.setenv("SYSTEMROOT","C:\\Windows")
    monkeypatch.setenv("LOAD_TEST_SECRET_SHOULD_NOT_PASS","no")
    environment=_safe_environment(Path("summary.json"))
    assert environment["SYSTEMROOT"]=="C:\\Windows"
    assert "LOAD_TEST_SECRET_SHOULD_NOT_PASS" not in environment
