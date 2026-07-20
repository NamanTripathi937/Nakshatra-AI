import http from 'k6/http';
import { sleep, check } from 'k6';
import { uuidv4 } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';

export const options = {
  stages: [
    { duration: '30s', target: 5 },  // Ramp up to 5 concurrent users over 30s
    { duration: '1m', target: 5 },   // Stay at 5 concurrent users for 1 minute
    { duration: '30s', target: 0 },  // Ramp down to 0 users
  ],
  thresholds: {
    http_req_failed: ['rate<0.05'],     // Less than 5% network/API errors
    http_req_duration: ['p(95)<8000'],  // 95% of requests should complete under 8s (generative LLM responses can be slow)
  },
};

export default function () {
  const sessionId = `k6-test-${uuidv4()}`;
  const baseUrl = __ENV.BASE_URL || 'http://localhost:8000';
  const headers = {
    'Content-Type': 'application/json',
    'X-Session-Id': sessionId,
  };

  // 1. Ping test (Raw performance check)
  let pingRes = http.get(`${baseUrl}/ping`, { headers });
  check(pingRes, { 'ping status is 200': (r) => r.status === 200 });
  sleep(1);

  // 2. Generate Kundli (Tests astro calculation engine + Mongo save)
  let kundliPayload = JSON.stringify({
    fullName: "K6 Load Tester",
    gender: "Female",
    dob: "1990-08-20",
    tob: "14:45:00",
    lat: 19.0760,
    lon: 72.8777,
    timezone: "Asia/Kolkata",
    place: "Mumbai, Maharashtra, India"
  });
  let kundliRes = http.post(`${baseUrl}/kundli`, kundliPayload, { headers });
  check(kundliRes, { 'kundli status is 200': (r) => r.status === 200 });
  sleep(2);

  // 3. Chat Messages (Loop to test rate limits and memory)
  for (let i = 0; i < 2; i++) {
    let chatPayload = JSON.stringify({
      query: `This is query number ${i + 1} from my load test. What does my chart say?`
    });
    let chatRes = http.post(`${baseUrl}/chat`, chatPayload, { headers });
    check(chatRes, {
      'chat status is 200': (r) => r.status === 200,
      'not daily limit (429)': (r) => r.status !== 429,
    });
    sleep(3);
  }
}
