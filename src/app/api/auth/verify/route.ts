import { NextRequest, NextResponse } from "next/server";
import { getToken } from "next-auth/jwt";
import { jwtVerify } from "jose";
import { prisma } from "@/lib/prisma";
import { checkCanProcess } from "@/lib/quota";

export async function GET(req: NextRequest) {
  let userId: string | null = null;

  const urlToken = req.nextUrl.searchParams.get("token");
  if (urlToken) {
    try {
      const secret = new TextEncoder().encode(process.env.NEXTAUTH_SECRET);
      const { payload } = await jwtVerify(urlToken, secret);
      userId = payload.sub as string;
    } catch {
      return new NextResponse(null, { status: 401 });
    }
  }

  if (!userId) {
    const token = await getToken({
      req,
      secret: process.env.NEXTAUTH_SECRET,
      secureCookie: req.headers.get("x-forwarded-proto") === "https",
    });
    userId = token?.sub ?? null;
  }

  if (!userId) {
    return new NextResponse(null, { status: 401 });
  }

  const quota = await checkCanProcess(userId);
  if (!quota.allowed) {
    return new NextResponse(null, { status: 403 });
  }

  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: { plan: true },
  });

  return new NextResponse(null, {
    status: 200,
    headers: {
      "X-User-Id": userId,
      "X-User-Plan": user?.plan ?? "FREE",
    },
  });
}
