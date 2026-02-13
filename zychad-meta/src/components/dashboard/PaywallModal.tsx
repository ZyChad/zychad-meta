"use client";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

const PLANS = [
  { name: "Starter", price: 29, priceYear: 28, features: ["200 fichiers/mois", "10 variantes", "IG Scraper"] },
  { name: "Pro", price: 79, priceYear: 63, features: ["1000 fichiers/mois", "50 variantes", "Mode Stealth", "API"] },
  { name: "Agency", price: 199, priceYear: 159, features: ["Illimité", "100 variantes", "5 seats"] },
];

export function PaywallModal({
  open,
  onOpenChange,
  reason,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  reason: string;
}) {
  const handleCheckout = (planKey: string, yearly: boolean) => {
    const priceId = yearly
      ? process.env.NEXT_PUBLIC_PADDLE_STARTER_YEARLY_PRICE_ID
      : process.env.NEXT_PUBLIC_PADDLE_STARTER_PRICE_ID;
    if (planKey === "PRO") {
      (window as unknown as { PADDLE?: { Checkout?: { open: (opts: object) => void } } }).PADDLE?.Checkout?.open?.({
        items: [{ priceId: yearly ? process.env.NEXT_PUBLIC_PADDLE_PRO_YEARLY_PRICE_ID : process.env.NEXT_PUBLIC_PADDLE_PRO_PRICE_ID }],
      });
    } else if (planKey === "AGENCY") {
      (window as unknown as { PADDLE?: { Checkout?: { open: (opts: object) => void } } }).PADDLE?.Checkout?.open?.({
        items: [{ priceId: yearly ? process.env.NEXT_PUBLIC_PADDLE_AGENCY_YEARLY_PRICE_ID : process.env.NEXT_PUBLIC_PADDLE_AGENCY_PRICE_ID }],
      });
    } else {
      (window as unknown as { PADDLE?: { Checkout?: { open: (opts: object) => void } } }).PADDLE?.Checkout?.open?.({
        items: [{ priceId }],
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent showClose={false} className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Tes 3 essais gratuits sont épuisés</DialogTitle>
          <DialogDescription>{reason || "Choisis un plan pour continuer à uniquifier."}</DialogDescription>
        </DialogHeader>
        <div className="grid md:grid-cols-3 gap-4 mt-4">
          {PLANS.map((plan) => (
            <Card key={plan.name} className="border-[var(--zychad-border)]">
              <CardHeader>
                <h3 className="font-semibold text-[var(--zychad-teal-bright)]">{plan.name}</h3>
                <p className="text-2xl font-bold text-[var(--zychad-text)]">{plan.price} €<span className="text-sm font-normal text-[var(--zychad-dim)]">/mois</span></p>
              </CardHeader>
              <CardContent className="space-y-3">
                <ul className="text-sm text-[var(--zychad-dim)] space-y-1">
                  {plan.features.map((f) => (
                    <li key={f}>• {f}</li>
                  ))}
                </ul>
                <Button
                  variant="teal"
                  className="w-full"
                  onClick={() => handleCheckout(plan.name.toUpperCase(), false)}
                >
                  Choisir {plan.name}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
