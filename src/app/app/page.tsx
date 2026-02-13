import { redirect } from "next/navigation";
import Link from "next/link";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import Link from "next/link";

export default async function AppPage() {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    redirect("/login?redirect=/app/");
  }

  const botUrl = process.env.BOT_URL ?? "http://localhost:61550";

  if (process.env.NODE_ENV === "development" && !process.env.USE_NGINX) {
    return (
      <div className="min-h-screen bg-[var(--zychad-bg)] flex items-center justify-center p-8">
        <div className="max-w-md text-center space-y-4">
          <h1 className="text-xl font-bold text-[var(--zychad-text)]">Mode développement</h1>
          <p className="text-[var(--zychad-dim)]">
            En production, <code className="text-[var(--teal)]">/app/</code> est servi par Nginx.
          </p>
          <p className="text-[var(--zychad-dim)]">
            En dev, lance le bot puis clique :
          </p>
            <a
              href={botUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block px-6 py-3 rounded-[10px] bg-[var(--teal)] text-[var(--bg)] font-medium hover:opacity-90"
            >
              Ouvrir le bot →
            </a>
          <p className="text-sm text-[var(--mut)]">
            <code>python zychad_metaV15.py</code> dans le dossier processing/
          </p>
          <Link href="/billing" className="block text-sm text-[var(--teal)]">
            ← Facturation
          </Link>
        </div>
      </div>
    );
  }

  const botUrl = process.env.BOT_URL ?? process.env.NEXT_PUBLIC_BOT_URL;
  if (botUrl) {
    redirect(botUrl);
  }

  // Bot non déployé : page d'attente
  return (
    <div className="min-h-screen bg-[var(--zychad-bg)] flex items-center justify-center p-8">
      <div className="max-w-md text-center space-y-6">
        <div className="w-16 h-16 mx-auto rounded-2xl bg-[var(--zychad-teal)]/20 flex items-center justify-center">
          <span className="text-3xl">⚡</span>
        </div>
        <h1 className="text-2xl font-bold text-[var(--zychad-text)]">
          Bot en cours de déploiement
        </h1>
        <p className="text-[var(--zychad-dim)]">
          L&apos;application d&apos;uniquification sera bientôt disponible ici. En attendant, utilise le dashboard.
        </p>
        <Link
          href="/dashboard"
          className="inline-block px-6 py-3 rounded-xl bg-[var(--zychad-teal)] text-[var(--zychad-bg)] font-semibold hover:opacity-90 transition"
        >
          Retour au dashboard
        </Link>
      </div>
    </div>
  );
}
