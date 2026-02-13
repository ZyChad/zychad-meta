import { NextRequest, NextResponse } from "next/server";
import { getToken } from "next-auth/jwt";
import { checkCanProcess } from "@/lib/quota";

export async function GET(req: NextRequest) {
  const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });
  const userId = token?.sub;
  if (!userId) {
    return NextResponse.json({ error: "Non autorisé" }, { status: 401 });
  }

  const quota = await checkCanProcess(userId);
  return NextResponse.json({
    allowed: quota.allowed,
    reason: quota.reason,
    shouldUpgrade: quota.shouldUpgrade,
  });
}
