import http from "k6/http";
import { check } from "k6";

const RATE = Number(__ENV.RATE || 100);
const HOT = Number(__ENV.HOT_RATIO || 0.9); // fraction of requests that hit cached keys

export const options = {
  scenarios: {
    step: {
      executor: "constant-arrival-rate",
      rate: RATE,
      timeUnit: "1s",
      duration: __ENV.DURATION || "20s",
      preAllocatedVUs: 200,
      maxVUs: 2000,
    },
  },
};

export default function () {
  // Hot keys 0-9 become cached after first use. Unique ids never repeat, so they always miss.
  const id =
    Math.random() < HOT
      ? Math.floor(Math.random() * 10)
      : 1000000 + Math.floor(Math.random() * 1e9);
  const res = http.get(`http://nginx/item/${id}`);
  check(res, { "status 200": (r) => r.status === 200 });
}

export function handleSummary(data) {
  const m = data.metrics;
  const dropped = m.dropped_iterations ? m.dropped_iterations.values.count : 0;
  const line =
    `rate=${RATE} achieved=${m.http_reqs.values.rate.toFixed(0)} ` +
    `p95=${m.http_req_duration.values["p(95)"].toFixed(0)}ms ` +
    `fail=${(m.http_req_failed.values.rate * 100).toFixed(1)}% dropped=${dropped}\n`;
  return { stdout: line };
}