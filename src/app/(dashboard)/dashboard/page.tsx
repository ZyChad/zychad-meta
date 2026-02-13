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
      {/* Gradient background (aligné bot) */}
      <div className="absolute inset-0 pointer-events-none -z-10">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_20%_0%,rgba(14,165,199,.06)_0%,transparent_60%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_80%_100%,rgba(6,182,212,.04)_0%,transparent_50%)]" />
      </div>

      <div className="p-8 md:p-12 max-w-4xl mx-auto">
        <h1 className="text-3xl md:text-4xl font-bold text-[var(--zychad-text)] mb-2 tracking-tight" style={{ fontFamily: "'Sora', sans-serif" }}>
          Tableau de bord
        </h1>
        <p className="text-xs text-[var(--zychad-dim)] mb-4">v2 • Accède au bot pour uniquifier</p>
        <p className="text-[var(--zychad-dim)] mb-10">
          Bienvenue sur ZyChad Meta. Accède au bot pour uniquifier tes contenus.
        </p>

        <div className="grid gap-4 md:grid-cols-3 mb-10">
          <div className="p-5 rounded-xl border border-[var(--br)] bg-[var(--s1)]">
            <p className="text-xs uppercase tracking-wider text-[var(--zychad-dim)] mb-1">Plan</p>
            <p className="text-2xl font-bold text-[var(--zychad-teal-bright)]">{user?.plan ?? "FREE"}</p>
          </div>
          <div className="p-5 rounded-xl border border-[var(--br)] bg-[var(--s1)]">
            <p className="text-xs uppercase tracking-wider text-[var(--zychad-dim)] mb-1">Fichiers traités</p>
            <p className="text-2xl font-bold text-[var(--zychad-text)]">{user?.filesProcessedTotal ?? 0}</p>
          </div>
          <div className="p-5 rounded-xl border border-[var(--br)] bg-[var(--s1)]">
            <p className="text-xs uppercase tracking-wider text-[var(--zychad-dim)] mb-1">Ce mois</p>
            <p className="text-2xl font-bold text-[var(--zychad-text)]">{user?.filesProcessedThisMonth ?? 0}</p>
          </div>
        </div>

        <div className="rounded-xl border border-[var(--br)] bg-[var(--s1)] p-8 md:p-10 text-center">
          <div className="w-16 h-16 mx-auto mb-6 rounded-xl bg-[rgba(14,165,199,.06)] border border-[rgba(14,165,199,.15)] flex items-center justify-center">
            <span className="text-3xl">⚡</span>
          </div>
          <h2 className="text-xl font-semibold text-[var(--zychad-text)] mb-2">
            Prêt à uniquifier ?
          </h2>
          <p className="text-[var(--zychad-dim)] mb-6 max-w-md mx-auto">
            Ouvre le bot pour uploader tes fichiers, choisir le mode et générer des variantes uniques.
          </p>
          <a
            href={botUrl ? `/api/bot-token?redirect=${encodeURIComponent(botUrl + "/")}` : "/app/"}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-lg bg-[var(--teal)] text-white font-semibold hover:bg-[var(--t2)] hover:shadow-[0_4px_20px_rgba(14,165,199,.25)] transition-all"
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
