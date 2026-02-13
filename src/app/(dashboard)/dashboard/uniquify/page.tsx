"use client";

import { useState, useEffect, useCallback } from "react";
import { useSession } from "next-auth/react";
import { UniquifyFlow } from "@/components/dashboard/UniquifyFlow";
import { PaywallModal } from "@/components/dashboard/PaywallModal";

export default function UniquifyPage() {
  const { data: session, status } = useSession();
  const [quotaBlocked, setQuotaBlocked] = useState<{ reason: string } | null>(null);

  useEffect(() => {
    if (status !== "authenticated" || !session?.user) return;

    const checkQuota = async () => {
      const res = await fetch("/api/quota/check");
      const data = await res.json();
      if (data.shouldUpgrade && !data.allowed) {
        setQuotaBlocked({ reason: data.reason ?? "Quota atteint" });
      }
    };

    checkQuota();
  }, [session, status]);

  const handleQuotaBlocked = useCallback((reason: string) => {
    setQuotaBlocked({ reason });
  }, []);

  if (quotaBlocked) {
    return (
      <>
        <div className="p-8 flex flex-col items-center justify-center min-h-[400px] text-center">
          <p className="text-lg text-[var(--zychad-text)] mb-4">{quotaBlocked.reason}</p>
          <p className="text-sm text-[var(--zychad-dim)] mb-6">Choisis un plan pour continuer à uniquifier.</p>
        </div>
        <PaywallModal
          open={true}
          onOpenChange={() => {}}
          reason={quotaBlocked.reason}
        />
      </>
    );
  }

  return (
    <div className="p-8 max-w-3xl">
      <h1 className="text-2xl font-bold text-[var(--zychad-text)] mb-2">Uniquifier</h1>
      <p className="text-[var(--zychad-dim)] mb-8">Upload tes fichiers et configure le traitement</p>
      <UniquifyFlow onQuotaBlocked={handleQuotaBlocked} />
    </div>
  );
}
