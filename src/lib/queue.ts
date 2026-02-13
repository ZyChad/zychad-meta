import { Queue } from "bullmq";

export type UniquifyJobData = {
  jobId: string;
  userId: string;
  inputFiles: { name: string; s3Key: string; size: number; type: string }[];
  variants: number;
  mode: string;
};

export type ScraperJobData = {
  scraperJobId: string;
  userId: string;
  platform: string;
  username: string;
  maxItems: number;
};

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

let _uniquifyQueue: Queue<UniquifyJobData> | null = null;
let _scraperQueue: Queue<ScraperJobData> | null = null;

export function getUniquifyQueue() {
  if (!_uniquifyQueue) {
    _uniquifyQueue = new Queue<UniquifyJobData>("uniquify", {
      connection: getRedisConnection(),
      defaultJobOptions: {
        removeOnComplete: { count: 1000 },
        removeOnFail: { count: 500 },
        attempts: 2,
        backoff: { type: "exponential", delay: 5000 },
      },
    });
  }
  return _uniquifyQueue;
}

export function getScraperQueue() {
  if (!_scraperQueue) {
    _scraperQueue = new Queue<ScraperJobData>("scraper", {
      connection: getRedisConnection(),
      defaultJobOptions: {
        removeOnComplete: { count: 500 },
        attempts: 1,
      },
    });
  }
  return _scraperQueue;
}

/** @deprecated Use getUniquifyQueue() - kept for backwards compat during migration */
export const uniquifyQueue = { add: (...args: Parameters<Queue["add"]>) => getUniquifyQueue().add(...args) };

/** @deprecated Use getScraperQueue() - kept for backwards compat during migration */
export const scraperQueue = { add: (...args: Parameters<Queue["add"]>) => getScraperQueue().add(...args) };
