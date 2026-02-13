import { NextRequest, NextResponse } from "next/server";
import { getToken } from "next-auth/jwt";
import { prisma } from "@/lib/prisma";
import { PLANS } from "@/lib/plans";
import type { PlanKey } from "@/lib/plans";

export async function GET(req: NextRequest) {
  const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });
  const userId = token?.sub;
  if (!userId) {
    return NextResponse.json({ error: "Non autorisé" }, { status: 401 });
  }

  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: { plan: true },
  });
  const planKey = (user?.plan ?? "FREE") as PlanKey;
  const plan = PLANS[planKey];

  return NextResponse.json({
    plan: planKey,
    maxVariants: plan.maxVariants,
    maxFileSize: plan.maxFileSize,
    modes: [...plan.modes],
    planName: plan.name,
  });
}
