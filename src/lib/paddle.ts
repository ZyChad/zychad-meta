import crypto from "crypto";

export function verifyPaddleWebhook(rawBody: string, signature: string): boolean {
  const secret = process.env.PADDLE_WEBHOOK_SECRET;
  if (!secret) return false;
  const parts = signature.split(";");
  const ts = parts.find((p) => p.startsWith("ts="))?.split("=")[1];
  const h1 = parts.find((p) => p.startsWith("h1="))?.split("=")[1];
  if (!ts || !h1) return false;
  const payload = `${ts}:${rawBody}`;
  const expected = crypto.createHmac("sha256", secret).update(payload).digest("hex");
  try {
    return crypto.timingSafeEqual(Buffer.from(h1, "utf8"), Buffer.from(expected, "utf8"));
  } catch {
    return false;
  }
}

export function getCheckoutPriceId(planKey: string, yearly: boolean): string | null {
  const envKey = yearly
    ? `PADDLE_${planKey}_YEARLY_PRICE_ID`
    : `PADDLE_${planKey}_PRICE_ID`;
  return process.env[envKey] ?? null;
}
