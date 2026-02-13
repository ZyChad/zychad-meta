import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default async function DashboardOverviewPage() {
  const session = await getServerSession(authOptions);
  const userId = (session?.user as { id?: string })?.id;
  if (!userId) return null;

  const [user, jobCount, recentJobs] = await Promise.all([
    prisma.user.findUnique({
      where: { id: userId },
      select: { plan: true, filesProcessedTotal: true, filesProcessedThisMonth: true },
    }),
    prisma.job.count({ where: { userId } }),
    prisma.job.findMany({
      where: { userId },
      orderBy: { createdAt: "desc" },
      take: 5,
      select: { id: true, status: true, createdAt: true },
    }),
  ]);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-[var(--zychad-text)] mb-6">Tableau de bord</h1>
      <div className="grid gap-4 md:grid-cols-3 mb-8">
        <div className="p-4 rounded-lg border border-[var(--zychad-border)] bg-[var(--zychad-surface)]">
          <p className="text-sm text-[var(--zychad-dim)]">Plan</p>
          <p className="text-xl font-semibold text-[var(--zychad-teal-bright)]">{user?.plan ?? "FREE"}</p>
        </div>
        <div className="p-4 rounded-lg border border-[var(--zychad-border)] bg-[var(--zychad-surface)]">
          <p className="text-sm text-[var(--zychad-dim)]">Jobs total</p>
          <p className="text-xl font-semibold text-[var(--zychad-text)]">{jobCount}</p>
        </div>
        <div className="p-4 rounded-lg border border-[var(--zychad-border)] bg-[var(--zychad-surface)]">
          <p className="text-sm text-[var(--zychad-dim)]">Ce mois</p>
          <p className="text-xl font-semibold text-[var(--zychad-text)]">{user?.filesProcessedThisMonth ?? 0} fichiers</p>
        </div>
      </div>
      <div className="rounded-lg border border-[var(--zychad-border)] bg-[var(--zychad-surface)] p-6">
        <h2 className="text-lg font-semibold text-[var(--zychad-text)] mb-4">Derniers jobs</h2>
        {recentJobs.length === 0 ? (
          <p className="text-[var(--zychad-dim)]">Aucun job pour l&apos;instant.</p>
        ) : (
          <ul className="space-y-2">
            {recentJobs.map((j) => (
              <li key={j.id} className="flex items-center justify-between text-sm">
                <span className="text-[var(--zychad-dim)]">{j.id.slice(0, 12)}…</span>
                <span className="text-[var(--zychad-text)]">{j.status}</span>
                <Link href={`/dashboard/history?job=${j.id}`}>
                  <Button variant="ghost" size="sm">Voir</Button>
                </Link>
              </li>
            ))}
          </ul>
        )}
        <div className="mt-6">
          <Link href="/dashboard/uniquify">
            <Button variant="teal">Nouvelle uniquification</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
