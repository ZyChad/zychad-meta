import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

/** API interne pour le bot : récupérer les paramètres Telegram d'un utilisateur */
export async function GET(req: NextRequest) {
  const secret = req.headers.get("X-Internal-Secret");
  if (secret !== process.env.INTERNAL_SECRET) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const userId = req.nextUrl.searchParams.get("userId");
  if (!userId) {
    return NextResponse.json({ error: "userId required" }, { status: 400 });
  }

  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: { telegramChatId: true, telegramTopicId: true },
  });

  if (!user) {
    return NextResponse.json({ error: "User not found" }, { status: 404 });
  }

  return NextResponse.json({
    tg_dest_chat_id: user.telegramChatId ?? "",
    tg_dest_topic_id: user.telegramTopicId ?? "",
  });
}

/** API interne pour le bot : sauvegarder les paramètres Telegram d'un utilisateur */
export async function POST(req: NextRequest) {
  const secret = req.headers.get("X-Internal-Secret");
  if (secret !== process.env.INTERNAL_SECRET) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const body = await req.json();
  const userId = body.userId as string;
  const tg_dest_chat_id = (body.tg_dest_chat_id as string) ?? "";
  const tg_dest_topic_id = (body.tg_dest_topic_id as string) ?? "";

  if (!userId) {
    return NextResponse.json({ error: "userId required" }, { status: 400 });
  }

  const user = await prisma.user.findUnique({ where: { id: userId } });
  if (!user) {
    return NextResponse.json({ error: "User not found" }, { status: 404 });
  }

  await prisma.user.update({
    where: { id: userId },
    data: {
      telegramChatId: tg_dest_chat_id || null,
      telegramTopicId: tg_dest_topic_id || null,
    },
  });

  return NextResponse.json({ ok: true });
}
