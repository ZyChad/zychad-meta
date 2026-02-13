import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import Link from "next/link";

export default async function DashboardOverviewPage() {
  const session = await getServerSession(authOptions);
  const userId = (session?.user as { id?: string })?.id;
  if (!userId) return null;

  const [user, jobCount] = await Promise.all([
    prisma.user.findUnique({
      where: { id: userId },
      select: { plan: true, filesProcessedTotal: true, filesProcessedThisMonth: true },
    }),
    prisma.job.count({ where: { userId } }),
  ]);

  const botUrl = process.env.BOT_URL ?? process.env.NEXT_PUBLIC_BOT_URL;

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Gradient background (style LP) */}
      <div className="absolute inset-0 pointer-events-none -z-10">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-[radial-gradient(ellipse_at_top,rgba(14,165,199,0.08)_0%,transparent_60%)]" />
      </div>

      <div className="p-8 md:p-12 max-w-4xl mx-auto">
        <h1 className="text-3xl md:text-4xl font-bold text-[var(--zychad-text)] mb-2 tracking-tight">
          Tableau de bord
        </h1>
        <p className="text-xs text-[var(--zychad-dim)] mb-4">v2 • Accède au bot pour uniquifier</p>
        <p className="text-[var(--zychad-dim)] mb-10">
          Bienvenue sur ZyChad Meta. Accède au bot pour uniquifier tes contenus.
        </p>

        <div className="grid gap-4 md:grid-cols-3 mb-10">
          <div className="p-5 rounded-2xl border border-[var(--zychad-border)] bg-[var(--zychad-surface)]/80 backdrop-blur-sm">
            <p className="text-xs uppercase tracking-wider text-[var(--zychad-dim)] mb-1">Plan</p>
            <p className="text-2xl font-bold text-[var(--zychad-teal-bright)]">{user?.plan ?? "FREE"}</p>
          </div>
          <div className="p-5 rounded-2xl border border-[var(--zychad-border)] bg-[var(--zychad-surface)]/80 backdrop-blur-sm">
            <p className="text-xs uppercase tracking-wider text-[var(--zychad-dim)] mb-1">Fichiers traités</p>
            <p className="text-2xl font-bold text-[var(--zychad-text)]">{user?.filesProcessedTotal ?? 0}</p>
          </div>
          <div className="p-5 rounded-2xl border border-[var(--zychad-border)] bg-[var(--zychad-surface)]/80 backdrop-blur-sm">
            <p className="text-xs uppercase tracking-wider text-[var(--zychad-dim)] mb-1">Ce mois</p>
            <p className="text-2xl font-bold text-[var(--zychad-text)]">{user?.filesProcessedThisMonth ?? 0}</p>
          </div>
        </div>

        <div className="rounded-2xl border border-[var(--zychad-border)] bg-[var(--zychad-surface)]/80 backdrop-blur-sm p-8 md:p-10 text-center">
          <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-[var(--zychad-teal)]/30 to-[var(--zychad-teal)]/10 flex items-center justify-center">
            <span className="text-3xl">⚡</span>
          </div>
          <h2 className="text-xl font-semibold text-[var(--zychad-text)] mb-2">
            Prêt à uniquifier ?
          </h2>
          <p className="text-[var(--zychad-dim)] mb-6 max-w-md mx-auto">
            Ouvre le bot pour uploader tes fichiers, choisir le mode et générer des variantes uniques.
          </p>
          <a
            href={botUrl || "/app/"}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-gradient-to-r from-[var(--zychad-teal)] to-[#0891b2] text-white font-semibold shadow-[0_6px_30px_rgba(14,165,199,0.35)] hover:shadow-[0_12px_44px_rgba(14,165,199,0.45)] hover:-translate-y-0.5 transition-all"
          >
            ⚡ Accéder au bot
          </a>
        </div>

        <div className="mt-8 flex flex-wrap gap-4 justify-center">
          <Link
            href="/dashboard/billing"
            className="text-sm text-[var(--zychad-dim)] hover:text-[var(--zychad-teal-bright)] transition"
          >
            Facturation →
          </Link>
          <Link
            href="/dashboard/settings"
            className="text-sm text-[var(--zychad-dim)] hover:text-[var(--zychad-teal-bright)] transition"
          >
            Paramètres →
          </Link>
        </div>
      </div>
    </div>
  );
}
