import Link from "next/link";
import { Button } from "@/components/ui/button";

export function CTA() {
  return (
    <section className="container mx-auto px-4 py-24 border-t border-[var(--zychad-border)]">
      <div className="max-w-2xl mx-auto text-center rounded-2xl border border-[var(--zychad-border)] bg-[var(--zychad-surface)] p-12">
        <h2 className="text-2xl md:text-3xl font-bold text-[var(--zychad-text)] mb-4">
          Prêt à uniquifier ?
        </h2>
        <p className="text-[var(--zychad-dim)] mb-8">
          3 essais gratuits, sans engagement. Passe à un plan quand tu veux.
        </p>
        <Link href="/register">
          <Button variant="teal" size="lg">
            Créer mon compte
          </Button>
        </Link>
      </div>
    </section>
  );
}
