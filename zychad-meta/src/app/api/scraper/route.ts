import { NextRequest, NextResponse } from "next/server";
import { getToken } from "next-auth/jwt";
import { prisma } from "@/lib/prisma";
import { scraperQueue } from "@/lib/queue";
import { rateLimit } from "@/lib/rate-limit";
import { PLANS } from "@/lib/plans";
import type { PlanKey } from "@/lib/plans";

export async function POST(req: NextRequest) {
  const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });
  const userId = token?.sub;
  if (!userId) {
    return NextResponse.json({ error: "Non autorisé" }, { status: 401 });
  }

  const { success } = await rateLimit(userId, "api:scraper");
  if (!success) {
    return NextResponse.json({ error: "Quota scraper atteint" }, { status: 429 });
  }

  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: { plan: true, scraperCallsThisMonth: true },
  });
  const plan = user?.plan ? PLANS[user.plan as PlanKey] : null;
  const limit = plan && "scraperLimit" in plan ? plan.scraperLimit : 0;
  if (limit === 0 || (limit !== -1 && (user?.scraperCallsThisMonth ?? 0) >= limit)) {
    return NextResponse.json({ error: "Scraper non disponible pour ton plan" }, { status: 403 });
  }

  const body = await req.json();
  const { platform, username } = body as { platform: string; username: string };
  if (!platform || !username) {
    return NextResponse.json({ error: "platform et username requis" }, { status: 400 });
  }

  const scraperJob = await prisma.scraperJob.create({
    data: { userId, platform, username, status: "pending" },
  });
  await scraperQueue.add("scrape", {
    scraperJobId: scraperJob.id,
    userId,
    platform,
    username,
    maxItems: 50,
  });

  return NextResponse.json({ jobId: scraperJob.id });
}
