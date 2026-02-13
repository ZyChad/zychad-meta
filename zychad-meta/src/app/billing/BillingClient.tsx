"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { PLANS } from "@/lib/plans";
import type { PlanKey } from "@/lib/plans";

const PLAN_KEYS: PlanKey[] = ["STARTER", "PRO", "AGENCY"];

export function BillingClient({
  userId,
  userEmail,
  paddleCustomerId,
}: {
  userId: string;
  userEmail: string;
  paddleCustomerId?: string;
}) {
  const [yearly, setYearly] = useState(false);
  const [paddle, setPaddle] = useState<unknown>(null);

  useEffect(() => {
    const init = async () => {
      const token = process.env.NEXT_PUBLIC_PADDLE_CLIENT_TOKEN;
      if (!token) return;
      try {
        const { initializePaddle } = await import("@paddle/paddle-js");
        const p = await initializePaddle({
          environment: (process.env.NEXT_PUBLIC_PADDLE_ENV as "sandbox" | "production") ?? "sandbox",
          token,
        });
        setPaddle(p);
      } catch {}
    };
    init();
  }, []);

  const openCheckout = (planKey: PlanKey) => {
    if (!paddle) return;
    const plan = PLANS[planKey];
    const priceId = yearly
      ? (plan as { paddlePriceIdYearly?: string }).paddlePriceIdYearly
      : (plan as { paddlePriceId?: string }).paddlePriceId;
    if (!priceId) return;
    (paddle as { Checkout: { open: (opts: unknown) => void } }).Checkout.open({
      items: [{ priceId, quantity: 1 }],
      customer: { email: userEmail },
      customData: { userId },
      settings: {
        successUrl: `${window.location.origin}/billing?success=true`,
        displayMode: "overlay",
        theme: "dark",
        locale: "fr",
      },
    });
  };

  const openPortal = () => {
    if (!paddle || !paddleCustomerId) return;
    (paddle as { Checkout: { open: (opts: unknown) => void } }).Checkout.open({
      customer: { id: paddleCustomerId },
      settings: {
        displayMode: "overlay",
        theme: "dark",
        locale: "fr",
      },
    });
  };

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-lg font-semibold text-[var(--txt)] mb-4">Choisis ton plan</h2>
        <div className="flex items-center gap-3 mb-6">
          <span className={!yearly ? "text-[var(--txt)] font-medium" : "text-[var(--dim)]"}>
            Mensuel
          </span>
          <button
            type="button"
            onClick={() => setYearly(!yearly)}
            className="w-11 h-6 rounded-full bg-[var(--s2)] relative"
            style={{ background: yearly ? "var(--teal)" : "var(--s2)" }}
          >
            <span
              className="absolute top-1 left-1 w-4 h-4 rounded-full bg-white transition-transform"
              style={{ transform: yearly ? "translateX(20px)" : "translateX(0)" }}
            />
          </button>
          <span className={yearly ? "text-[var(--txt)] font-medium" : "text-[var(--dim)]"}>
            Annuel <span className="text-[var(--grn)] text-sm">-20%</span>
          </span>
        </div>

        <div className="grid sm:grid-cols-3 gap-4">
          {PLAN_KEYS.map((key) => {
            const p = PLANS[key];
            const price = yearly ? Math.round((p.price as number) * 0.8) : p.price;
            return (
              <div
                key={key}
                className="p-6 rounded-xl border border-[rgba(20,51,69,.4)] bg-[var(--s1)]"
              >
                <h3 className="font-semibold text-[var(--teal)]">{p.name}</h3>
                <p className="text-2xl font-bold text-[var(--txt)] mt-2">
                  {price} €<span className="text-sm font-normal text-[var(--dim)]">/mois</span>
                </p>
                <ul className="mt-4 space-y-1 text-sm text-[var(--dim)]">
                  {[...p.features].slice(0, 3).map((f) => (
                    <li key={f}>• {f}</li>
                  ))}
                </ul>
                <Button
                  variant="teal"
                  className="w-full mt-4 rounded-[10px]"
                  onClick={() => openCheckout(key)}
                >
                  Choisir {p.name}
                </Button>
              </div>
            );
          })}
        </div>
      </div>

      {paddleCustomerId && (
        <div>
          <Button variant="outline" onClick={openPortal} className="rounded-[10px]">
            Gérer l&apos;abonnement (Paddle Portal)
          </Button>
        </div>
      )}

      <p className="text-sm text-[var(--dim)]">
        <Link href="/app/" className="text-[var(--teal)] hover:underline">
          ← Retour à l&apos;app
        </Link>
      </p>
    </div>
  );
}
