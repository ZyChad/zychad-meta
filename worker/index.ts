import { Worker } from "bullmq";
import { processUniquifyJob } from "./uniquify";

function getRedisConnection() {
  const url = process.env.REDIS_URL ?? "redis://localhost:6379";
  try {
    const u = new URL(url);
    return {
      host: u.hostname,
      port: parseInt(u.port, 10) || 6379,
      password: u.password || undefined,
    };
  } catch {
    return { host: "localhost", port: 6379 };
  }
}

const connection = getRedisConnection();

const worker = new Worker(
  "uniquify",
  async (job) => {
    const { jobId, userId, inputFiles, variants, mode } = job.data;
    await processUniquifyJob({ jobId, userId, inputFiles, variants, mode });
  },
  { connection, concurrency: 2 }
);

worker.on("completed", (job) => {
  console.log(`[worker] Job ${job.id} completed`);
});

worker.on("failed", (job, err) => {
  console.error(`[worker] Job ${job?.id} failed:`, err);
});

async function main() {
  console.log("[worker] Uniquify worker started");
}

main().catch(console.error);
