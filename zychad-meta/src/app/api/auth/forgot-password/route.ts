import { NextRequest, NextResponse } from "next/server";
import { rateLimit } from "@/lib/rate-limit";

export async function POST(req: NextRequest) {
  const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? "127.0.0.1";
  const { success } = await rateLimit(ip, "auth:login");
  if (!success) {
    return NextResponse.json({ error: "Trop de tentatives." }, { status: 429 });
  }

  const { email } = await req.json();
  if (!email) {
    return NextResponse.json({ error: "Email requis." }, { status: 400 });
  }

  // TODO: table PasswordResetToken + envoi email (Resend/SendGrid)
  return NextResponse.json({ ok: true });
}
