import Link from "next/link";

export const metadata = {
  title: "Contact — ZyChad Meta",
  description: "Contactez l'équipe ZyChad Meta.",
};

export default function ContactPage() {
  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--tx)]">
      <header className="border-b border-[var(--br)] py-6">
        <div className="max-w-3xl mx-auto px-6">
          <Link href="/" className="text-[var(--t3)] hover:underline font-semibold">
            ← Retour
          </Link>
        </div>
      </header>
      <main className="max-w-3xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold text-[var(--tx)] mb-2">Contact</h1>
        <p className="text-[var(--dm)] mb-10">
          Une question, un problème ou une suggestion ? Envoyez-nous un message.
        </p>

        <div className="rounded-xl border border-[var(--br)] bg-[var(--s1)] p-8 space-y-6">
          <p className="text-[var(--dm)]">
            Pour nous contacter, envoyez un email à :{" "}
            <a
              href="mailto:contact@zychadmeta.com"
              className="text-[var(--t3)] hover:underline font-medium"
            >
              contact@zychadmeta.com
            </a>
          </p>
          <p className="text-sm text-[var(--mut)]">
            Nous nous efforçons de répondre sous 48 heures ouvrées. Pour les questions liées à
            la facturation ou aux remboursements, précisez votre email de compte et la référence
            de facturation.
          </p>
        </div>
      </main>
      <footer className="border-t border-[var(--br)] py-6 mt-12">
        <div className="max-w-3xl mx-auto px-6 text-center text-sm text-[var(--mut)]">
          <Link href="/" className="text-[var(--t3)] hover:underline">
            ZyChad Meta
          </Link>
          {" · "}
          <Link href="/conditions" className="text-[var(--dm)] hover:underline">
            Conditions
          </Link>
          {" · "}
          <Link href="/confidentialite" className="text-[var(--dm)] hover:underline">
            Confidentialité
          </Link>
          {" · "}
          <Link href="/remboursement" className="text-[var(--dm)] hover:underline">
            Remboursement
          </Link>
        </div>
      </footer>
    </div>
  );
}
