import { NextRequest, NextResponse } from "next/server";
import { verifyPaddleWebhook } from "@/lib/paddle";
import { prisma } from "@/lib/prisma";
import { PLANS } from "@/lib/plans";
import type { PlanKey } from "@/lib/plans";

function getPlanFromPriceId(priceId: string): PlanKey {
  for (const [key, p] of Object.entries(PLANS)) {
    if ("paddlePriceId" in p && p.paddlePriceId === priceId) return key as PlanKey;
    if ("paddlePriceIdYearly" in p && p.paddlePriceIdYearly === priceId) return key as PlanKey;
  }
  return "FREE";
}

export async function POST(req: NextRequest) {
  const rawBody = await req.text();
  const signature = req.headers.get("paddle-signature") ?? "";
  if (!verifyPaddleWebhook(rawBody, signature)) {
    return NextResponse.json({ error: "Invalid signature" }, { status: 401 });
  }

  const event = JSON.parse(rawBody) as { event_type: string; data: Record<string, unknown> };

  switch (event.event_type) {
    case "subscription.created":
    case "subscription.updated": {
      const sub = event.data as {
        customer_id: string;
        id: string;
        status: string;
        items?: { price?: { id: string } }[];
        current_billing_period?: { ends_at: string };
        custom_data?: { userId?: string };
      };
      const priceId = sub.items?.[0]?.price?.id ?? "";
      const plan = getPlanFromPriceId(priceId);
      const updateData = {
        plan,
        subscriptionStatus: sub.status,
        paddleCustomerId: sub.customer_id,
        paddleSubscriptionId: sub.id,
        subscriptionEnd: sub.current_billing_period?.ends_at
          ? new Date(sub.current_billing_period.ends_at)
          : null,
      };
      if (sub.custom_data?.userId) {
        await prisma.user.update({
          where: { id: sub.custom_data.userId },
          data: updateData,
        });
      } else {
        await prisma.user.updateMany({
          where: { paddleCustomerId: sub.customer_id },
          data: updateData,
        });
      }
      break;
    }
    case "subscription.canceled": {
      const data = event.data as { customer_id: string };
      await prisma.user.updateMany({
        where: { paddleCustomerId: data.customer_id },
        data: {
          plan: "FREE",
          subscriptionStatus: "canceled",
          paddleSubscriptionId: null,
        },
      });
      break;
    }
    case "transaction.completed": {
      const data = event.data as { customer_id: string };
      await prisma.user.updateMany({
        where: { paddleCustomerId: data.customer_id },
        data: {
          filesProcessedThisMonth: 0,
          scraperCallsThisMonth: 0,
          quotaResetDate: new Date(),
        },
      });
      break;
    }
    case "subscription.past_due": {
      const data = event.data as { customer_id: string };
      await prisma.user.updateMany({
        where: { paddleCustomerId: data.customer_id },
        data: { subscriptionStatus: "past_due" },
      });
      break;
    }
  }

  return NextResponse.json({ received: true });
}
