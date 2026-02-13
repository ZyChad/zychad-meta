import { NextRequest, NextResponse } from "next/server";
import { getToken } from "next-auth/jwt";
import { prisma } from "@/lib/prisma";
import { checkCanProcess } from "@/lib/quota";

export async function GET(req: NextRequest) {
  const token = await getToken({
    req,
    secret: process.env.NEXTAUTH_SECRET,
    secureCookie: req.headers.get("x-forwarded-proto") === "https",
  });

  if (!token?.sub) {
    return new NextResponse(null, { status: 401 });
  }

  const quota = await checkCanProcess(token.sub);
  if (!quota.allowed) {
    return new NextResponse(null, { status: 403 });
  }

  const user = await prisma.user.findUnique({
    where: { id: token.sub },
    select: { plan: true },
  });

  return new NextResponse(null, {
    status: 200,
    headers: {
      "X-User-Id": token.sub,
      "X-User-Plan": user?.plan ?? "FREE",
    },
  });
}
