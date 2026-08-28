from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import AppError


def _binary() -> str:
    configured=settings.k6_binary_path.strip() or "k6"
    resolved=shutil.which(configured)
    if not resolved and Path(configured).is_file():resolved=str(Path(configured).resolve())
    if not resolved:raise AppError("K6_NOT_AVAILABLE","The managed k6 engine is not installed on the server.",503)
    return resolved


def _safe_environment(summary_path:Path)->dict[str,str]:
    # Keep only runtime and proxy settings. Some hosted/enterprise networks
    # require an outbound proxy; dropping these values made k6 fail even though
    # the application's preflight request and the browser could reach the URL.
    allowed={"path","systemroot","windir","temp","tmp","home","userprofile","ssl_cert_file","ssl_cert_dir","http_proxy","https_proxy","no_proxy"}
    # Windows environment-variable names are case-insensitive. Preserve the
    # actual spelling supplied by the host (commonly SYSTEMROOT), otherwise
    # k6 cannot use the Windows DNS resolver.
    environment={key:value for key,value in os.environ.items() if key.casefold() in allowed}
    environment.update({"K6_NO_USAGE_REPORT":"true","K6_SUMMARY_EXPORT":str(summary_path)})
    return environment


def execute_generated_k6(script:str,plan_id:str)->dict:
    if not script or "AI Web Hosting Advisor" not in script or "http.get" not in script:
        raise AppError("K6_SCRIPT_INVALID","The server-generated k6 scenario is unavailable or invalid.",500)
    storage=Path(settings.load_test_storage_dir)/"managed-runs";storage.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"{plan_id[:8]}-",dir=storage) as temporary:
        directory=Path(temporary);script_path=directory/"scenario.js";summary_path=directory/"summary.json"
        script_path.write_text(script,encoding="utf-8")
        command=[_binary(),"run","--quiet","--no-color","--new-machine-readable-summary","--summary-mode","full","--summary-trend-stats","avg,min,med,max,p(90),p(95),p(99)",str(script_path)]
        try:
            completed=subprocess.run(command,cwd=directory,env=_safe_environment(summary_path),capture_output=True,text=True,timeout=settings.managed_load_test_execution_timeout_seconds,check=False)
        except subprocess.TimeoutExpired as exc:
            raise AppError("K6_RUN_TIMEOUT","The bounded k6 test exceeded the server execution time limit.",504) from exc
        if not summary_path.is_file():
            detail=(completed.stderr or completed.stdout or "k6 did not create a summary").strip()[-600:]
            raise AppError("K6_RUN_FAILED",f"k6 could not create a test result: {detail}",502)
        if summary_path.stat().st_size>settings.k6_result_max_file_mb*1024*1024:
            raise AppError("K6_RESULT_TOO_LARGE","The generated k6 summary exceeded the configured result limit.",500)
        try:data=json.loads(summary_path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError,json.JSONDecodeError) as exc:raise AppError("K6_RESULT_INVALID","k6 produced an unreadable summary.",502) from exc
        data["advisor_execution"]={"engine":"k6","exitCode":completed.returncode,"thresholdExit":completed.returncode!=0,"planId":plan_id}
        return data
