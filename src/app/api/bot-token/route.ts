import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { checkCanProcess } from "@/lib/quota";
import { SignJWT } from "jose";
import { NextRequest, NextResponse } from "next/server";

const BOT_URL = process.env.BOT_URL ?? process.env.NEXT_PUBLIC_BOT_URL ?? "https://app.zychadmeta.com";
const TOKEN_TTL = 5 * 60; // 5 minutes

export async function GET(req: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.redirect(new URL("/login?redirect=" + encodeURIComponent(BOT_URL + "/"), req.url));
  }

  const userId = (session.user as { id?: string }).id;
  if (!userId) return NextResponse.redirect(new URL("/login", req.url));

  const quota = await checkCanProcess(userId);
  if (!quota.allowed) {
    return NextResponse.redirect(new URL("/billing?reason=quota", req.url));
  }

  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: { plan: true },
  });

  const secret = new TextEncoder().encode(process.env.NEXTAUTH_SECRET);
  const token = await new SignJWT({
    sub: userId,
    plan: user?.plan ?? "FREE",
  })
    .setProtectedHeader({ alg: "HS256" })
    .setExpirationTime(`${TOKEN_TTL}s`)
    .sign(secret);

  const redirectTo = req.nextUrl.searchParams.get("redirect") || BOT_URL;
  const url = new URL(redirectTo);
  url.searchParams.set("token", token);

  return NextResponse.redirect(url);
}
