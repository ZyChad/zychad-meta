import { NextRequest, NextResponse } from "next/server";
import { getToken } from "next-auth/jwt";
import { prisma } from "@/lib/prisma";
import { uniquifyQueue } from "@/lib/queue";
import { checkCanProcess } from "@/lib/quota";
import { createJobSchema } from "@/lib/security";
import { rateLimit } from "@/lib/rate-limit";
import { PLANS } from "@/lib/plans";
import type { PlanKey } from "@/lib/plans";

export async function GET(req: NextRequest) {
  const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });
  const userId = token?.sub;
  if (!userId) {
    return NextResponse.json({ error: "Non autorisé" }, { status: 401 });
  }

  const { searchParams } = new URL(req.url);
  const page = Math.max(1, parseInt(searchParams.get("page") ?? "1", 10));
  const limit = Math.min(50, Math.max(1, parseInt(searchParams.get("limit") ?? "20", 10)));
  const offset = (page - 1) * limit;

  const [jobs, total] = await Promise.all([
    prisma.job.findMany({
      where: { userId },
      orderBy: { createdAt: "desc" },
      skip: offset,
      take: limit,
    }),
    prisma.job.count({ where: { userId } }),
  ]);

  return NextResponse.json({
    jobs,
    total,
    page,
    limit,
  });
}

export async function POST(req: NextRequest) {
  const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });
  const userId = token?.sub;
  if (!userId) {
    return NextResponse.json({ error: "Non autorisé" }, { status: 401 });
  }

  const { success } = await rateLimit(userId, "api:job");
  if (!success) {
    return NextResponse.json({ error: "Trop de jobs. Réessaie dans 1 min." }, { status: 429 });
  }

  const quota = await checkCanProcess(userId);
  if (!quota.allowed) {
    return NextResponse.json(
      { error: quota.reason, shouldUpgrade: quota.shouldUpgrade },
      { status: 403 }
    );
  }

  const body = await req.json();
  const parsed = createJobSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: "Données invalides", details: parsed.error.flatten() },
      { status: 400 }
    );
  }

  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: { plan: true },
  });
  const plan = user?.plan ? PLANS[user.plan as PlanKey] : null;
  const maxVariants = plan && "maxVariants" in plan ? plan.maxVariants : 3;
  const modes = plan && "modes" in plan ? [...plan.modes] : ["normal"];
  if (parsed.data.variants > maxVariants) {
    return NextResponse.json(
      { error: `Maximum ${maxVariants} variantes pour ton plan` },
      { status: 400 }
    );
  }
  if (!modes.includes(parsed.data.mode)) {
    return NextResponse.json(
      { error: `Mode "${parsed.data.mode}" non disponible pour ton plan` },
      { status: 400 }
    );
  }

  const retentionHours = plan && "retentionHours" in plan ? plan.retentionHours : 6;
  const expiresAt = new Date(Date.now() + retentionHours * 60 * 60 * 1000);

  const job = await prisma.job.create({
    data: {
      userId,
      status: "PENDING",
      inputFiles: parsed.data.files,
      variants: parsed.data.variants,
      mode: parsed.data.mode,
      total: parsed.data.files.length * parsed.data.variants,
      expiresAt,
    },
  });

  await uniquifyQueue.add(
    "uniquify",
    {
      jobId: job.id,
      userId,
      inputFiles: parsed.data.files,
      variants: parsed.data.variants,
      mode: parsed.data.mode,
    },
    { jobId: job.id }
  );

  return NextResponse.json({ job });
}
