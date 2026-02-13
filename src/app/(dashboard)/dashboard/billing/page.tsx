import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { PLANS } from "@/lib/plans";
import type { PlanKey } from "@/lib/plans";

export default async function BillingPage() {
  const session = await getServerSession(authOptions);
  const userId = (session?.user as { id?: string })?.id;
  if (!userId) return null;

  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: {
      plan: true,
      subscriptionStatus: true,
      subscriptionEnd: true,
      filesProcessedThisMonth: true,
      filesProcessedTotal: true,
    },
  });

  const plan = user?.plan ? PLANS[user.plan as PlanKey] : null;
  const monthlyLimit = plan && "filesPerMonth" in plan ? plan.filesPerMonth : 3;

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-[var(--zychad-text)] mb-6">Facturation</h1>
      <div className="space-y-6 max-w-2xl">
        <div className="p-4 rounded-lg border border-[var(--zychad-border)] bg-[var(--zychad-surface)]">
          <p className="text-sm text-[var(--zychad-dim)]">Plan actuel</p>
          <p className="text-xl font-semibold text-[var(--zychad-teal-bright)]">{user?.plan ?? "FREE"}</p>
          <p className="text-sm text-[var(--zychad-dim)] mt-1">
            Statut : {user?.subscriptionStatus ?? "—"}
          </p>
          {user?.subscriptionEnd && (
            <p className="text-sm text-[var(--zychad-dim)]">
              Renouvellement : {new Date(user.subscriptionEnd).toLocaleDateString("fr-FR")}
            </p>
          )}
        </div>
        <div className="p-4 rounded-lg border border-[var(--zychad-border)] bg-[var(--zychad-surface)]">
          <p className="text-sm text-[var(--zychad-dim)]">Utilisation ce mois</p>
          <p className="text-xl font-semibold text-[var(--zychad-text)]">
            {user?.filesProcessedThisMonth ?? 0}
            {typeof monthlyLimit === "number" && monthlyLimit !== -1 && (
              <span className="text-sm font-normal text-[var(--zychad-dim)]"> / {monthlyLimit} fichiers</span>
            )}
          </p>
        </div>
        <div className="p-4 rounded-lg border border-[var(--zychad-border)] bg-[var(--zychad-surface)]">
          <p className="text-sm text-[var(--zychad-dim)]">Total à vie</p>
          <p className="text-xl font-semibold text-[var(--zychad-text)]">{user?.filesProcessedTotal ?? 0} fichiers</p>
        </div>
        <p className="text-sm text-[var(--zychad-dim)]">
          Gère ton abonnement depuis le portail Paddle après ton achat.
        </p>
      </div>
    </div>
  );
}
