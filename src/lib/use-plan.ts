"use client";

import { useState, useEffect } from "react";

export type PlanInfo = {
  plan: string;
  maxVariants: number;
  maxFileSize: number;
  modes: string[];
  planName: string;
};

export function usePlan(): PlanInfo | null {
  const [plan, setPlan] = useState<PlanInfo | null>(null);

  useEffect(() => {
    fetch("/api/user/plan")
      .then((r) => r.json())
      .then(setPlan)
      .catch(() => setPlan(null));
  }, []);

  return plan;
}
