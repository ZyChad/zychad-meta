import { NextRequest, NextResponse } from "next/server";
import { getToken } from "next-auth/jwt";
import { prisma } from "@/lib/prisma";
import { presignDownload } from "@/lib/s3";
import { rateLimit } from "@/lib/rate-limit";

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });
  const userId = token?.sub;
  if (!userId) {
    return NextResponse.json({ error: "Non autorisé" }, { status: 401 });
  }

  const { success } = await rateLimit(userId, "api:download");
  if (!success) {
    return NextResponse.json({ error: "Trop de téléchargements" }, { status: 429 });
  }

  const { id } = await params;
  const job = await prisma.job.findFirst({
    where: { id, userId },
    select: { outputZipKey: true },
  });
  if (!job?.outputZipKey) {
    return NextResponse.json({ error: "Fichier introuvable" }, { status: 404 });
  }

  const url = await presignDownload(job.outputZipKey, 3600);
  return NextResponse.json({ url });
}
