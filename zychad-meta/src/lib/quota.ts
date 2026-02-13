import { prisma } from "./prisma";
import { PLANS, FREE_TRIAL_QUOTA } from "./plans";
import type { PlanKey } from "./plans";

export async function checkCanProcess(userId: string): Promise<{
  allowed: boolean;
  reason?: string;
  shouldUpgrade: boolean;
}> {
  const user = await prisma.user.findUnique({ where: { id: userId } });
  if (!user) return { allowed: false, reason: "Utilisateur introuvable", shouldUpgrade: false };

  const plan = PLANS[user.plan as PlanKey];

  if (user.plan === "FREE") {
    if (user.filesProcessedTotal >= FREE_TRIAL_QUOTA) {
      return {
        allowed: false,
        reason: `Tu as utilisé tes ${FREE_TRIAL_QUOTA} uniquifications gratuites. Choisis un plan pour continuer.`,
        shouldUpgrade: true,
      };
    }
    return { allowed: true, shouldUpgrade: false };
  }

  if (plan && "filesPerMonth" in plan && plan.filesPerMonth !== -1 && user.filesProcessedThisMonth >= plan.filesPerMonth) {
    return {
      allowed: false,
      reason: `Quota mensuel atteint (${plan.filesPerMonth} fichiers). Passe à un plan supérieur ou attends le mois prochain.`,
      shouldUpgrade: true,
    };
  }

  if (user.subscriptionStatus !== "active" && user.subscriptionStatus !== "trialing") {
    return {
      allowed: false,
      reason: "Ton abonnement n'est plus actif. Renouvelle-le pour continuer.",
      shouldUpgrade: true,
    };
  }

  return { allowed: true, shouldUpgrade: false };
}
