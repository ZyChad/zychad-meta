import { NextRequest, NextResponse } from "next/server";
import { getToken } from "next-auth/jwt";
import { getUploadKey, presignUpload } from "@/lib/s3";
import { checkCanProcess } from "@/lib/quota";
import { validateFilename, isAllowedMime } from "@/lib/security";
import { rateLimit } from "@/lib/rate-limit";
import { prisma } from "@/lib/prisma";
import { PLANS } from "@/lib/plans";
import type { PlanKey } from "@/lib/plans";

export async function POST(req: NextRequest) {
  const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });
  const userId = token?.sub ?? req.headers.get("x-api-key") ? await getUserIdFromApiKey(req) : null;
  if (!userId) {
    return NextResponse.json({ error: "Non autorisé" }, { status: 401 });
  }

  const { success } = await rateLimit(userId, "api:upload");
  if (!success) {
    return NextResponse.json({ error: "Trop d'uploads. Réessaie dans 1 min." }, { status: 429 });
  }

  const quota = await checkCanProcess(userId);
  if (!quota.allowed) {
    return NextResponse.json({ error: quota.reason, shouldUpgrade: quota.shouldUpgrade }, { status: 403 });
  }

  const body = await req.json();
  const { filename, contentType, jobId } = body as { filename: string; contentType: string; jobId: string };
  if (!filename || !contentType || !jobId) {
    return NextResponse.json({ error: "filename, contentType et jobId requis" }, { status: 400 });
  }

  const valid = validateFilename(filename);
  if (!valid.ok) {
    return NextResponse.json({ error: valid.error }, { status: 400 });
  }
  if (!isAllowedMime(contentType)) {
    return NextResponse.json({ error: "Type de fichier non autorisé" }, { status: 400 });
  }

  const user = await prisma.user.findUnique({ where: { id: userId }, select: { plan: true } });
  const plan = user?.plan ? PLANS[user.plan as PlanKey] : null;
  const maxSize = plan && "maxFileSize" in plan ? plan.maxFileSize : 50 * 1024 * 1024;

  const key = getUploadKey(userId, jobId, filename);
  const uploadUrl = await presignUpload(key, contentType);

  return NextResponse.json({
    uploadUrl,
    key,
    maxSize,
  });
}

async function getUserIdFromApiKey(req: NextRequest): Promise<string | null> {
  const apiKey = req.headers.get("x-api-key");
  if (!apiKey) return null;
  const crypto = await import("crypto");
  const hash = crypto.createHash("sha256").update(apiKey).digest("hex");
  const user = await prisma.user.findFirst({
    where: { apiKeyHash: hash },
    select: { id: true },
  });
  return user?.id ?? null;
}
