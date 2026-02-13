#!/usr/bin/env node
/**
 * Smoke test : vérifie que l'app répond correctement
 * Usage: npm run dev (dans un terminal) puis node scripts/smoke-test.js
 */

const http = require("http");

const BASE = process.env.BASE_URL || "http://localhost:3000";

const TIMEOUT_MS = 8000;

function fetch(path, opts = {}) {
  return new Promise((resolve, reject) => {
    const u = new URL(path, BASE);
    const req = http.request(
      u,
      { method: opts.method || "GET", ...opts },
      (res) => {
        let body = "";
        res.on("data", (c) => (body += c));
        res.on("end", () => resolve({ status: res.statusCode, body }));
      }
    );
    req.on("error", reject);
    req.setTimeout(TIMEOUT_MS, () => {
      req.destroy();
      reject(new Error("Timeout"));
    });
    if (opts.body) req.write(typeof opts.body === "string" ? opts.body : JSON.stringify(opts.body));
    req.end();
  });
}

async function run() {
  const results = [];
  const ok = (name, cond) => {
    results.push({ name, ok: !!cond });
    console.log(cond ? `  ✓ ${name}` : `  ✗ ${name}`);
  };

  console.log("\nZyChad Meta - Smoke tests\n");

  try {
    const r = await fetch("/api/health");
    ok("GET /api/health", r.status === 200 && r.body.includes("ok"));
  } catch (e) {
    ok("GET /api/health", false);
    console.error("  → Démarre l'app avec: npm run dev");
    process.exit(1);
  }

  try {
    const r = await fetch("/");
    ok("GET / (landing)", r.status === 200);
  } catch {
    ok("GET /", false);
  }

  try {
    const r = await fetch("/login");
    ok("GET /login", r.status === 200);
  } catch {
    ok("GET /login", false);
  }

  try {
    const r = await fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: `test-${Date.now()}@example.com`,
        password: "TestPass123!",
        name: "Test",
      }),
    });
    ok("POST /api/auth/register", r.status === 200 || r.status === 201);
  } catch (e) {
    ok("POST /api/auth/register", false);
  }

  const passed = results.filter((r) => r.ok).length;
  console.log(`\n${passed}/${results.length} tests OK\n`);
  process.exit(passed === results.length ? 0 : 1);
}

run().catch((e) => {
  console.error(e);
  process.exit(1);
});
