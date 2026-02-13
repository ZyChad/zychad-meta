import { NextRequest, NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import crypto from "crypto";
import { prisma } from "@/lib/prisma";
import { rateLimit } from "@/lib/rate-limit";
import { sendVerificationEmail } from "@/lib/email";

export async function POST(req: NextRequest) {
  const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? req.headers.get("x-real-ip") ?? "127.0.0.1";
  const { success } = await rateLimit(ip, "auth:register");
  if (!success) {
    return NextResponse.json(
      { error: "Trop d'inscriptions. Réessaie dans 1 heure." },
      { status: 429 }
    );
  }

  const body = await req.json();
  const email = (body.email as string)?.toLowerCase()?.trim();
  const password = body.password as string;
  const name = (body.name as string)?.trim();

  if (!email || !password) {
    return NextResponse.json(
      { error: "Email et mot de passe requis." },
      { status: 400 }
    );
  }
  if (password.length < 8) {
    return NextResponse.json(
      { error: "Le mot de passe doit faire au moins 8 caractères." },
      { status: 400 }
    );
  }

  const existing = await prisma.user.findUnique({ where: { email } });
  if (existing) {
    return NextResponse.json(
      { error: "Un compte existe déjà avec cet email." },
      { status: 400 }
    );
  }

  const passwordHash = await bcrypt.hash(password, 12);
  const requiresVerification = !!process.env.RESEND_API_KEY;
  const token = requiresVerification ? crypto.randomBytes(32).toString("hex") : null;
  const expires = requiresVerification ? new Date(Date.now() + 24 * 60 * 60 * 1000) : null;

  await prisma.user.create({
    data: {
      email,
      name: name || null,
      passwordHash,
      plan: "FREE",
      emailVerificationToken: token,
      emailVerificationExpires: expires,
    },
  });

  if (requiresVerification && token) {
    await sendVerificationEmail(email, token);
  }

  return NextResponse.json({
    ok: true,
    requiresVerification,
  });
}
