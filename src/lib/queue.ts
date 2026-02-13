import { Queue } from "bullmq";

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

export const uniquifyQueue = new Queue("uniquify", {
  connection,
  defaultJobOptions: {
    removeOnComplete: { count: 1000 },
    removeOnFail: { count: 500 },
    attempts: 2,
    backoff: { type: "exponential", delay: 5000 },
  },
});

export const scraperQueue = new Queue("scraper", {
  connection,
  defaultJobOptions: {
    removeOnComplete: { count: 500 },
    attempts: 1,
  },
});

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
