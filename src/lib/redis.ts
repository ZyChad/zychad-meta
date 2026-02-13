import Redis from "ioredis";

const redisUrl = process.env.REDIS_URL ?? "redis://localhost:6379";

function createRedis(): Redis {
  return new Redis(redisUrl, {
    maxRetriesPerRequest: null,
    enableReadyCheck: true,
    retryStrategy: (times) => Math.min(times * 50, 2000),
    lazyConnect: true,
  });
}

const globalForRedis = globalThis as unknown as { redis: Redis };

export const redis = globalForRedis.redis ?? createRedis();
redis.on("error", () => {}); // évite les AggregateError non gérées quand Redis est absent

if (process.env.NODE_ENV !== "production") globalForRedis.redis = redis;
