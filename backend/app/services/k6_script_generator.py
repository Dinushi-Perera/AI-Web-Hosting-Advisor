from __future__ import annotations
import json,re
from datetime import datetime,timezone
from app.core.config import settings

GENERATOR_VERSION="k6-generator-1.1.0"

def safe_filename(title:str,public_id:str)->str:
    slug=re.sub(r"[^a-z0-9]+","-",title.lower()).strip("-")[:80] or "project"
    return f"{slug}-load-test-{public_id[:8]}.js"

def generate_script(*,project_title:str,project_id:str,target_url:str,test_type:str,context:dict,plan:dict,p95_ms:int,error_rate:float,think_min:int,think_max:int,safe_paths:list[str],host_overrides:dict[str,str]|None=None,execution_mode:str="MANUAL")->str:
    stages=[{"duration":f"{s['duration_seconds']}s","target":s["target_virtual_users"]} for s in plan["stages"]]
    weights=max(1,len(safe_paths));paths=json.dumps(safe_paths)
    return f'''/*
AI Web Hosting Advisor — authorized manual k6 scenario
Project: {project_title}
Project ID: {project_id}
Generated: {datetime.now(timezone.utc).isoformat()}
Test Type: {test_type}
Expected Users: {context['expected_concurrent_users']}
Target VUs: {plan['target_virtual_users']}
Estimated RPS: {context['estimated_rps']}
Peak RPS: {context['peak_rps']}
AI Recommendation: {context['ai_context']['hosting']}
Resource Recommendation: {context['ai_context']['vcpu']} vCPU / {context['ai_context']['ram_gb']} GB RAM
PageSpeed Performance: {context.get('performance_context',{}).get('performance_score') if context.get('performance_context',{}).get('available') else 'Unavailable'}
IMPORTANT: Run only against systems you own or have explicit permission to test.
Execution Mode: {execution_mode}
*/
import http from 'k6/http';
import {{ check, sleep }} from 'k6';

export const options = {{
  stages: {json.dumps(stages,indent=2)},
  hosts: {json.dumps(host_overrides or {},indent=2)},
  userAgent: 'AIHostingAdvisor-k6/1.1',
  thresholds: {{
    http_req_failed: ['rate<{error_rate}'],
    http_req_duration: ['p(95)<{p95_ms}', 'p(99)<{settings.k6_default_p99_threshold_ms}'],
    checks: ['rate>{settings.k6_default_check_pass_rate}'],
  }},
}};

const BASE_URL = {json.dumps(target_url.rstrip('/'))};
const SAFE_PATHS = {paths};
function randomIntBetween(min, max) {{ return Math.floor(Math.random() * (max - min + 1)) + min; }}

export default function () {{
  const path = SAFE_PATHS[(__VU + __ITER) % SAFE_PATHS.length];
  const response = http.get(`${{BASE_URL}}${{path}}`, {{ redirects: {settings.k6_max_redirects}, timeout: '30s' }});
  check(response, {{
    'status is successful': (r) => r.status >= 200 && r.status < 400,
    'response time is acceptable': (r) => r.timings.duration < {p95_ms},
  }});
  sleep(randomIntBetween({think_min}, {think_max}));
}}
'''
