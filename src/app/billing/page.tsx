import { redirect } from "next/navigation";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { PLANS } from "@/lib/plans";
import type { PlanKey } from "@/lib/plans";
import { BillingClient } from "./BillingClient";

export default async function BillingPage({
  searchParams,
}: {
  searchParams: Promise<{ reason?: string }>;
}) {
  const session = await getServerSession(authOptions);
  const userId = (session?.user as { id?: string })?.id;
  if (!userId) {
    redirect("/login?redirect=/billing");
  }

  const params = await searchParams;
  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: {
      plan: true,
      subscriptionStatus: true,
      subscriptionEnd: true,
      filesProcessedThisMonth: true,
      filesProcessedTotal: true,
      paddleCustomerId: true,
    },
  });

  const plan = user?.plan ? PLANS[user.plan as PlanKey] : null;
  const monthlyLimit = plan && "filesPerMonth" in plan ? plan.filesPerMonth : 3;
  const used = user?.plan === "FREE" ? user?.filesProcessedTotal ?? 0 : user?.filesProcessedThisMonth ?? 0;

  return (
    <div className="min-h-screen bg-[var(--zychad-bg)] p-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-2xl font-bold text-[var(--zychad-text)] mb-6">Facturation</h1>

        {params.reason === "quota" && (
          <div className="mb-6 p-4 rounded-xl border border-[var(--zychad-red)]/30 bg-[var(--zychad-red)]/10 text-[var(--zychad-red)]">
            Quota dépassé. Upgrade ton plan pour continuer à uniquifier.
          </div>
        )}

        <div className="space-y-6 mb-8">
          <div className="p-6 rounded-xl border border-[rgba(20,51,69,.4)] bg-[var(--s1)]">
            <p className="text-sm text-[var(--dim)]">Plan actuel</p>
            <p className="text-xl font-semibold text-[var(--teal)]">{user?.plan ?? "FREE"}</p>
            <p className="text-sm text-[var(--dim)] mt-1">
              Statut : {user?.subscriptionStatus ?? "—"}
            </p>
            {user?.subscriptionEnd && (
              <p className="text-sm text-[var(--dim)]">
                Renouvellement : {new Date(user.subscriptionEnd).toLocaleDateString("fr-FR")}
              </p>
            )}
          </div>
          <div className="p-6 rounded-xl border border-[rgba(20,51,69,.4)] bg-[var(--s1)]">
            <p className="text-sm text-[var(--dim)]">Utilisation</p>
            <p className="text-xl font-semibold text-[var(--txt)]">
              {used}
              {typeof monthlyLimit === "number" && monthlyLimit !== -1 && (
                <span className="text-sm font-normal text-[var(--dim)]"> / {monthlyLimit} fichiers</span>
              )}
              {user?.plan === "FREE" && (
                <span className="text-sm font-normal text-[var(--dim)]"> / 3 à vie</span>
              )}
            </p>
            {typeof monthlyLimit === "number" && monthlyLimit !== -1 && (
              <div className="mt-2 h-2 rounded-full bg-[var(--s2)] overflow-hidden">
                <div
                  className="h-full rounded-full bg-[var(--teal)]"
                  style={{ width: `${Math.min(100, (used / monthlyLimit) * 100)}%` }}
                />
              </div>
            )}
          </div>
        </div>

        <BillingClient
          userId={userId}
          userEmail={(session?.user as { email?: string })?.email ?? ""}
          paddleCustomerId={user?.paddleCustomerId ?? undefined}
        />
      </div>
    </div>
  );
}
