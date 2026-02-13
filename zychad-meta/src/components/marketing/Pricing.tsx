"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

const PLANS = [
  {
    name: "Starter",
    priceMonth: 29,
    priceYear: 28,
    desc: "200 fichiers/mois, 10 variantes, IG Scraper",
    features: ["200 fichiers/mois", "10 variantes max", "Mode Normal + Double", "IG Scraper"],
  },
  {
    name: "Pro",
    priceMonth: 79,
    priceYear: 63,
    desc: "1000 fichiers/mois, 50 variantes, Stealth, API",
    features: ["1000 fichiers/mois", "50 variantes", "Mode Stealth", "IG + TikTok", "API", "Scheduler"],
  },
  {
    name: "Agency",
    priceMonth: 199,
    priceYear: 159,
    desc: "Illimité, 100 variantes, 5 seats",
    features: ["Fichiers illimités", "100 variantes", "5 seats", "Support Telegram dédié"],
  },
];

export function Pricing() {
  const [yearly, setYearly] = useState(false);

  return (
    <section className="container mx-auto px-4 py-20 border-t border-[var(--zychad-border)]" id="pricing">
      <h2 className="text-3xl font-bold text-center mb-4 text-[var(--zychad-text)]">
        Tarifs
      </h2>
      <p className="text-center text-[var(--zychad-dim)] mb-8">
        Commence gratuitement — 3 uniquifications offertes, sans carte
      </p>
      <div className="flex items-center justify-center gap-3 mb-10">
        <span className={!yearly ? "text-[var(--zychad-text)] font-medium" : "text-[var(--zychad-dim)]"}>Mensuel</span>
        <button
          type="button"
          role="switch"
          aria-checked={yearly}
          onClick={() => setYearly(!yearly)}
          className="w-11 h-6 rounded-full bg-[var(--zychad-border)] relative data-[state=checked]:bg-[var(--zychad-teal)]"
          style={{ background: yearly ? "var(--zychad-teal)" : "var(--zychad-border)" }}
        >
          <span
            className="absolute top-1 left-1 w-4 h-4 rounded-full bg-white transition-transform"
            style={{ transform: yearly ? "translateX(20px)" : "translateX(0)" }}
          />
        </button>
        <span className={yearly ? "text-[var(--zychad-text)] font-medium" : "text-[var(--zychad-dim)]"}>
          Annuel <span className="text-[var(--zychad-green)] text-sm">-20%</span>
        </span>
      </div>
      <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
        {PLANS.map((plan) => (
          <Card key={plan.name} className="border-[var(--zychad-border)]">
            <CardHeader>
              <h3 className="text-xl font-semibold text-[var(--zychad-teal-bright)]">{plan.name}</h3>
              <p className="text-sm text-[var(--zychad-dim)]">{plan.desc}</p>
              <p className="text-2xl font-bold text-[var(--zychad-text)]">
                {yearly ? plan.priceYear : plan.priceMonth} €
                <span className="text-sm font-normal text-[var(--zychad-dim)]">/mois</span>
              </p>
            </CardHeader>
            <CardContent className="space-y-4">
              <ul className="space-y-2 text-sm text-[var(--zychad-dim)]">
                {plan.features.map((f) => (
                  <li key={f}>• {f}</li>
                ))}
              </ul>
              <Link href="/register">
                <Button variant="teal" className="w-full">
                  Choisir {plan.name}
                </Button>
              </Link>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
}
