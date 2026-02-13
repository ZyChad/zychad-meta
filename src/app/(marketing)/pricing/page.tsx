import { Pricing } from "@/components/marketing/Pricing";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-[var(--zychad-bg)]">
      <header className="border-b border-[var(--zychad-border)] py-4">
        <div className="container mx-auto px-4 flex items-center justify-between">
          <Link href="/" className="text-xl font-bold text-[var(--zychad-teal-bright)]">⚡ ZyChad Meta</Link>
          <div className="flex gap-4">
            <Link href="/login"><Button variant="ghost">Connexion</Button></Link>
            <Link href="/register"><Button variant="teal">S'inscrire</Button></Link>
          </div>
        </div>
      </header>
      <main className="py-12">
        <Pricing />
      </main>
    </div>
  );
}
