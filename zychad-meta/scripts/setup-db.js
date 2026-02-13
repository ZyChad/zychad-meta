#!/usr/bin/env node
/**
 * Script pour obtenir une base PostgreSQL gratuite (Instagres/Neon)
 * et configurer .env automatiquement.
 * Usage: node scripts/setup-db.js
 */

const https = require("https");
const fs = require("fs");
const path = require("path");

const ENV_PATH = path.join(__dirname, "..", ".env");

async function fetchInstagres() {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify({ ref: "zychad-meta" });
    const req = https.request(
      {
        hostname: "instagres.com",
        path: "/api/v1/database",
        method: "POST",
        headers: { "Content-Type": "application/json", "Content-Length": data.length },
      },
      (res) => {
        let body = "";
        res.on("data", (chunk) => (body += chunk));
        res.on("end", () => {
          try {
            resolve(JSON.parse(body));
          } catch {
            reject(new Error("Réponse invalide"));
          }
        });
      }
    );
    req.on("error", reject);
    req.write(data);
    req.end();
  });
}

function updateEnv(connectionString) {
  let content = fs.readFileSync(ENV_PATH, "utf8");
  const urlMatch = content.match(/^DATABASE_URL=.*$/m);
  if (urlMatch) {
    content = content.replace(urlMatch[0], `DATABASE_URL=${connectionString}`);
  } else {
    content = content.replace(/\n/, `\nDATABASE_URL=${connectionString}\n`);
  }
  fs.writeFileSync(ENV_PATH, content);
}

async function main() {
  console.log("Récupération d'une base PostgreSQL gratuite (Instagres)...");
  try {
    const result = await fetchInstagres();
    const conn = result.connection_string || result.connectionString;
    if (!conn) {
      console.error("Pas de connection_string dans la réponse:", result);
      process.exit(1);
    }
    updateEnv(conn);
    console.log("DATABASE_URL mis à jour dans .env");
    if (result.claim_url) {
      console.log("\nPour garder la base permanent: " + result.claim_url);
    }
    process.exit(0);
  } catch (err) {
    console.error("Erreur:", err.message);
    console.log("\nAlternative: crée un projet sur neon.tech et copie l'URL dans .env");
    process.exit(1);
  }
}

main();
