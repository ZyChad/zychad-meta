import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function POST(req: NextRequest) {
  const secret = req.headers.get("X-Internal-Secret");
  if (secret !== process.env.INTERNAL_SECRET) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const body = await req.json();
  const userId = body.userId as string;
  const filesCount = (body.filesCount as number) ?? 1;

  if (!userId) {
    return NextResponse.json({ error: "userId required" }, { status: 400 });
  }

  const user = await prisma.user.findUnique({ where: { id: userId } });
  if (!user) {
    return NextResponse.json({ error: "User not found" }, { status: 404 });
  }

  if (user.plan === "FREE") {
    await prisma.user.update({
      where: { id: userId },
      data: { filesProcessedTotal: { increment: filesCount } },
    });
  } else {
    await prisma.user.update({
      where: { id: userId },
      data: {
        filesProcessedThisMonth: { increment: filesCount },
        quotaResetDate: new Date(),
      },
    });
  }

  return NextResponse.json({ ok: true });
}
