import Redis from "ioredis";

const redisUrl = process.env.REDIS_URL ?? "redis://localhost:6379";

const globalForRedis = globalThis as unknown as { redis: Redis | null };

function createRedis(): Redis {
  const client = new Redis(redisUrl, {
    maxRetriesPerRequest: null,
    enableReadyCheck: true,
    retryStrategy: (times) => Math.min(times * 50, 2000),
    lazyConnect: true,
  });
  client.on("error", () => {}); // évite les AggregateError non gérées quand Redis est absent
  return client;
}

/** Lazy Redis client - only connects when first used (avoids connection during Vercel build) */
export function getRedis(): Redis {
  if (!globalForRedis.redis) {
    globalForRedis.redis = createRedis();
  }
  return globalForRedis.redis;
}
