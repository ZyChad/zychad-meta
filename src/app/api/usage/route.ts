import { NextRequest, NextResponse } from "next/server";
import { getToken } from "next-auth/jwt";
import { prisma } from "@/lib/prisma";
import { PLANS, FREE_TRIAL_QUOTA } from "@/lib/plans";
import type { PlanKey } from "@/lib/plans";

export async function GET(req: NextRequest) {
  const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });
  const userId = token?.sub;
  if (!userId) {
    return NextResponse.json({ error: "Non autorisé" }, { status: 401 });
  }

  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: {
      plan: true,
      filesProcessedTotal: true,
      filesProcessedThisMonth: true,
    },
  });

  if (!user) {
    return NextResponse.json({ error: "User not found" }, { status: 404 });
  }

  const plan = PLANS[user.plan as PlanKey];
  const limit =
    user.plan === "FREE"
      ? FREE_TRIAL_QUOTA
      : plan && "filesPerMonth" in plan
        ? plan.filesPerMonth
        : 0;
  const used =
    user.plan === "FREE"
      ? user.filesProcessedTotal
      : user.filesProcessedThisMonth;

  return NextResponse.json({
    plan: user.plan,
    used,
    limit: limit === -1 ? null : limit,
    remaining: limit === -1 ? null : Math.max(0, limit - used),
  });
}
