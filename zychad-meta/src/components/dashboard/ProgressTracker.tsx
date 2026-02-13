"use client";

import { useEffect, useState } from "react";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";

export function ProgressTracker({
  jobId,
  onComplete,
  onCancel,
}: {
  jobId: string;
  onComplete: () => void;
  onCancel?: () => void;
}) {
  const [status, setStatus] = useState("");
  const [progress, setProgress] = useState(0);
  const [total, setTotal] = useState(0);
  const [currentFile, setCurrentFile] = useState("");
  const [error, setError] = useState("");
  const [outputZipKey, setOutputZipKey] = useState<string | null>(null);

  useEffect(() => {
    const evt = new EventSource(`/api/jobs/${jobId}/stream`);
    evt.onmessage = (e) => {
      try {
        const d = JSON.parse(e.data);
        setStatus(d.status ?? "");
        setProgress(d.progress ?? 0);
        setTotal(d.total ?? 0);
        setCurrentFile(d.currentFile ?? "");
        setError(d.error ?? "");
        setOutputZipKey(d.outputZipKey ?? null);
        if (d.status === "COMPLETED" || d.status === "FAILED" || d.status === "CANCELLED") {
          evt.close();
          if (d.status === "COMPLETED") onComplete();
        }
      } catch {}
    };
    evt.onerror = () => evt.close();
    return () => evt.close();
  }, [jobId, onComplete]);

  const pct = total > 0 ? Math.round((progress / total) * 100) : 0;

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="rounded-xl border border-[rgba(20,51,69,.4)] bg-[var(--s1)] p-6 space-y-4">
        <p className="text-sm text-[var(--dim)]">
          {status} — {progress}/{total} ({pct}%)
        </p>
        <Progress
          value={pct}
          className="h-3 [&>div]:bg-gradient-to-r [&>div]:from-[var(--teal)] [&>div]:to-[var(--grn)]"
        />
        {currentFile && (
          <p className="text-sm text-[var(--txt)] font-mono">Fichier en cours : {currentFile}</p>
        )}
        {error && (
          <p className="text-sm text-[var(--red)]">Erreur : {error}</p>
        )}
        {status === "COMPLETED" && outputZipKey && (
          <p className="text-sm text-[var(--grn)]">Terminé ! Télécharge le ZIP ci-dessous.</p>
        )}
        {onCancel && status !== "COMPLETED" && status !== "FAILED" && (
          <Button
            variant="ghost"
            size="sm"
            className="text-[var(--dim)] hover:text-[var(--red)]"
            onClick={onCancel}
          >
            Annuler
          </Button>
        )}
      </div>
    </div>
  );
}
