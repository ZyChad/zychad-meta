import Link from "next/link";
import { Button } from "@/components/ui/button";

export function Hero() {
  return (
    <section className="container mx-auto px-4 py-24 md:py-32">
      <div className="max-w-3xl mx-auto text-center space-y-8">
        <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-[var(--zychad-text)]">
          Uniquifie tes vidéos et images en un clic
        </h1>
        <p className="text-lg md:text-xl text-[var(--zychad-dim)] max-w-2xl mx-auto">
          Plus de 25 techniques appliquées côté serveur pour rendre ton contenu unique et éviter les détections. Idéal pour le repost sur les réseaux.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link href="/register">
            <Button variant="teal" size="lg" className="w-full sm:w-auto">
              Commence gratuitement — 3 essais offerts
            </Button>
          </Link>
          <Link href="/pricing">
            <Button variant="outline" size="lg" className="w-full sm:w-auto border-[var(--zychad-border)] text-[var(--zychad-text)]">
              Voir les tarifs
            </Button>
          </Link>
        </div>
      </div>
    </section>
  );
}
