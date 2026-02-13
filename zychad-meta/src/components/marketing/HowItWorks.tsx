import Link from "next/link";
import { Button } from "@/components/ui/button";

const STEPS = [
  { n: 1, title: "Crée ton compte", desc: "Inscription en 30 secondes, sans carte bancaire." },
  { n: 2, title: "Teste gratuitement", desc: "3 uniquifications offertes pour essayer." },
  { n: 3, title: "Choisis ton plan", desc: "Starter, Pro ou Agency selon tes besoins." },
];

export function HowItWorks() {
  return (
    <section className="container mx-auto px-4 py-20 border-t border-[var(--zychad-border)]">
      <h2 className="text-3xl font-bold text-center mb-12 text-[var(--zychad-text)]">
        Comment ça marche
      </h2>
      <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
        {STEPS.map((s) => (
          <div key={s.n} className="text-center">
            <div className="w-12 h-12 rounded-full bg-[var(--zychad-teal)] text-[var(--zychad-bg)] font-bold flex items-center justify-center mx-auto mb-4">
              {s.n}
            </div>
            <h3 className="text-lg font-semibold text-[var(--zychad-text)] mb-2">{s.title}</h3>
            <p className="text-sm text-[var(--zychad-dim)]">{s.desc}</p>
          </div>
        ))}
      </div>
      <div className="text-center mt-10">
        <Link href="/register">
          <Button variant="teal" size="lg">Commencer maintenant</Button>
        </Link>
      </div>
    </section>
  );
}
