import http from 'k6/http';
import { check, sleep } from 'k6';

// Safe local installation check. This file never targets a public website.
// Start the frontend first, then run: k6 run .\load_tests\test.js
const target = __ENV.TARGET_URL || 'http://127.0.0.1:3000/';

export const options = {
  vus: 1,
  duration: '10s',
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<2000'],
    checks: ['rate==1'],
  },
};

export default function () {
  const response = http.get(target, {
    redirects: 0,
    tags: { scenario: 'local_smoke_test' },
  });

  check(response, {
    'local frontend returns HTTP 200': (result) => result.status === 200,
  });
  sleep(1);
}
