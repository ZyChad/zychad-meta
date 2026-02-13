import { Pricing } from "@/components/marketing/Pricing";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { LOGO_DATA_URL } from "@/lib/brand";

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-[var(--zychad-bg)]">
      <header className="border-b border-[var(--zychad-border)] py-4">
        <div className="container mx-auto px-4 flex items-center justify-between">
          <Link href="/" className="text-xl font-bold text-[var(--t2)] flex items-center gap-2">
            <img src={LOGO_DATA_URL} alt="ZyChad Meta" className="w-10 h-10 rounded-[10px]" />
            ZyChad Meta
          </Link>
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
