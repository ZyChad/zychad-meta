import { getRedis } from "./redis";

const WINDOWS: Record<string, { windowSec: number; max: number }> = {
  "api:global": { windowSec: 60, max: 100 },
  "api:upload": { windowSec: 60, max: 20 },
  "api:job": { windowSec: 60, max: 10 },
  "api:scraper": { windowSec: 3600, max: 10 },
  "auth:login": { windowSec: 900, max: 5 },
  "auth:register": { windowSec: 3600, max: 3 },
  "api:download": { windowSec: 60, max: 30 },
};

export async function rateLimit(
  key: string,
  windowKey: keyof typeof WINDOWS
): Promise<{ success: boolean; remaining: number }> {
  const config = WINDOWS[windowKey];
  if (!config) return { success: true, remaining: 999 };

  try {
    const fullKey = `rl:${windowKey}:${key}`;
    const now = Math.floor(Date.now() / 1000);
    const windowStart = now - config.windowSec;

    const multi = getRedis().multi();
    multi.zremrangebyscore(fullKey, 0, windowStart);
    multi.zadd(fullKey, now, `${now}:${Math.random()}`);
    multi.zcard(fullKey);
    multi.expire(fullKey, config.windowSec * 2);

    const results = await Promise.race([
      multi.exec(),
      new Promise<null>((_, rej) => setTimeout(() => rej(new Error("Redis timeout")), 2000)),
    ]);
    const count = (results?.[2]?.[1] as number) ?? 0;
    const remaining = Math.max(0, config.max - count);
    const success = count <= config.max;

    if (!success && results?.[1]) {
      await getRedis().zrem(fullKey, (results[1] as [Error | null, string[]])[1]?.[0]);
    }

    return { success, remaining };
  } catch {
    return { success: true, remaining: 999 };
  }
}
