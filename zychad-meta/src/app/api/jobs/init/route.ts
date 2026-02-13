import { NextRequest, NextResponse } from "next/server";
import { getToken } from "next-auth/jwt";
import { prisma } from "@/lib/prisma";
import { checkCanProcess } from "@/lib/quota";

export async function POST(req: NextRequest) {
  const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });
  const userId = token?.sub;
  if (!userId) {
    return NextResponse.json({ error: "Non autorisé" }, { status: 401 });
  }

  const quota = await checkCanProcess(userId);
  if (!quota.allowed) {
    return NextResponse.json(
      { error: quota.reason, shouldUpgrade: quota.shouldUpgrade },
      { status: 403 }
    );
  }

  const job = await prisma.job.create({
    data: {
      userId,
      status: "PENDING",
      inputFiles: [],
      variants: 3,
      mode: "normal",
    },
  });

  return NextResponse.json({ jobId: job.id });
}
