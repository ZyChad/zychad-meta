import { NextRequest, NextResponse } from "next/server";
import { getToken } from "next-auth/jwt";
import { prisma } from "@/lib/prisma";
import { uniquifyQueue } from "@/lib/queue";
import { PLANS } from "@/lib/plans";
import type { PlanKey } from "@/lib/plans";

export async function POST(req: NextRequest) {
  const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });
  const userId = token?.sub;
  if (!userId) {
    return NextResponse.json({ error: "Non autorisé" }, { status: 401 });
  }

  const body = await req.json();
  const { jobId, files, variants, mode } = body as {
    jobId: string;
    files: { name: string; s3Key: string; size: number; type: string }[];
    variants?: number;
    mode?: string;
  };
  if (!jobId || !Array.isArray(files) || files.length === 0) {
    return NextResponse.json({ error: "jobId et files requis" }, { status: 400 });
  }

  const job = await prisma.job.findFirst({
    where: { id: jobId, userId },
  });
  if (!job) {
    return NextResponse.json({ error: "Job introuvable" }, { status: 404 });
  }

  const nVariants = Math.min(100, Math.max(1, variants ?? 3));
  const nMode = mode && ["normal", "double", "stealth"].includes(mode) ? mode : "normal";

  const user = await prisma.user.findUnique({ where: { id: userId }, select: { plan: true } });
  const plan = user?.plan ? PLANS[user.plan as PlanKey] : null;
  const maxVariants = plan && "maxVariants" in plan ? plan.maxVariants : 3;
  const modes = plan && "modes" in plan ? [...plan.modes] : ["normal"];
  if (nVariants > maxVariants || !modes.includes(nMode)) {
    return NextResponse.json({ error: "Config invalide pour ton plan" }, { status: 400 });
  }

  await prisma.job.update({
    where: { id: jobId },
    data: {
      status: "UPLOADING",
      inputFiles: files,
      variants: nVariants,
      mode: nMode,
      total: files.length * nVariants,
    },
  });

  await uniquifyQueue.add(
    "uniquify",
    {
      jobId,
      userId,
      inputFiles: files,
      variants: nVariants,
      mode: nMode,
    },
    { jobId }
  );

  return NextResponse.json({ ok: true });
}
