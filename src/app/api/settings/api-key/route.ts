import { NextRequest, NextResponse } from "next/server";
import { getToken } from "next-auth/jwt";
import { prisma } from "@/lib/prisma";
import crypto from "crypto";

export async function POST(req: NextRequest) {
  const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });
  const userId = token?.sub;
  if (!userId) {
    return NextResponse.json({ error: "Non autorisé" }, { status: 401 });
  }

  const apiKey = `zc_${crypto.randomBytes(24).toString("hex")}`;
  const hash = crypto.createHash("sha256").update(apiKey).digest("hex");

  await prisma.user.update({
    where: { id: userId },
    data: { apiKey, apiKeyHash: hash },
  });

  return NextResponse.json({ key: apiKey });
}
