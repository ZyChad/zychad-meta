"use client";

import { useState, useCallback } from "react";
import { FileUploader } from "./FileUploader";
import { ProgressTracker } from "./ProgressTracker";
import { ResultsGallery } from "./ResultsGallery";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { usePlan } from "@/lib/use-plan";

type Step = "upload" | "config" | "processing" | "results";

export function UniquifyFlow({ onQuotaBlocked }: { onQuotaBlocked: (reason: string) => void }) {
  const plan = usePlan();
  const [step, setStep] = useState<Step>("upload");
  const [jobId, setJobId] = useState<string | null>(null);
  const [configJobId, setConfigJobId] = useState<string | null>(null);
  const [files, setFiles] = useState<{ name: string; s3Key: string; size: number; type: string }[]>([]);
  const [variants, setVariants] = useState(3);
  const [mode, setMode] = useState<"normal" | "double" | "stealth">("normal");
  const [error, setError] = useState("");

  const maxVariants = plan?.maxVariants ?? 3;
  const modes = plan?.modes ?? ["normal"];

  const handleFilesReady = useCallback((f: { name: string; s3Key: string; size: number; type: string }[], jId: string) => {
    setFiles(f);
    setConfigJobId(jId);
    setVariants((v) => Math.min(maxVariants, v));
    setStep("config");
  }, [maxVariants]);

  const handleStart = useCallback(async () => {
    if (!configJobId) return;
    setError("");
    try {
      const res = await fetch("/api/upload/complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          jobId: configJobId,
          files,
          variants,
          mode,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        if (data.shouldUpgrade) {
          onQuotaBlocked(data.error ?? "Quota atteint");
          return;
        }
        setError(data.error ?? "Erreur");
        return;
      }
      setJobId(configJobId);
      setStep("processing");
    } catch {
      setError("Erreur lors du lancement");
    }
  }, [configJobId, files, variants, mode, onQuotaBlocked]);

  const handleComplete = useCallback(() => {
    setStep("results");
  }, []);

  const handleReset = useCallback(() => {
    setStep("upload");
    setJobId(null);
    setConfigJobId(null);
    setFiles([]);
  }, []);

  if (step === "upload") {
    return (
      <FileUploader
        onComplete={handleFilesReady}
        onQuotaBlocked={onQuotaBlocked}
        maxFileSize={plan?.maxFileSize}
      />
    );
  }

  if (step === "config") {
    return (
      <div className="space-y-6 max-w-2xl">
        <div className="rounded-xl border border-[rgba(20,51,69,.4)] bg-[var(--s1)] p-6 space-y-6">
          <p className="text-[var(--dim)]">{files.length} fichier(s) sélectionné(s)</p>
          <div className="space-y-4">
            <Label className="text-[var(--txt)]">Nombre de variantes : {variants}</Label>
            <Slider
              value={[variants]}
              onValueChange={([v]) => setVariants(Math.min(maxVariants, v ?? 3))}
              min={1}
              max={maxVariants}
              step={1}
              className="[&_[data-slot=track]]:bg-[var(--s2)] [&_[data-slot=range]]:bg-[var(--teal)] [&_[data-slot=thumb]]:bg-[var(--teal)] [&_[data-slot=thumb]]:shadow-[0_0_12px_rgba(14,165,199,.5)]"
            />
            <p className="text-sm text-[var(--dim)]">Max {maxVariants} variantes ({plan?.planName ?? "Essai gratuit"})</p>
          </div>
          <div className="space-y-2">
            <Label className="text-[var(--txt)]">Mode de traitement</Label>
            <div className="flex gap-2 flex-wrap">
              {(["normal", "double", "stealth"] as const).map((m) => {
                const label = m === "normal" ? "Normal" : m === "double" ? "Double Process" : "Stealth";
                const available = modes.includes(m);
                return (
                  <Button
                    key={m}
                    variant={mode === m ? "teal" : "outline"}
                    size="sm"
                    onClick={() => available && setMode(m)}
                    disabled={!available}
                    title={!available ? "Upgrade to PRO" : undefined}
                    className="rounded-[10px]"
                  >
                    {label}
                  </Button>
                );
              })}
            </div>
            <p className="text-sm text-[var(--dim)]">25+ techniques d&apos;uniquification</p>
          </div>
        </div>
        {error && <p className="text-sm text-[var(--red)]">{error}</p>}
        <div className="flex gap-4">
          <Button variant="outline" onClick={() => setStep("upload")} className="rounded-[10px]">
            Retour
          </Button>
          <Button
            variant="teal"
            onClick={handleStart}
            className="rounded-[10px] bg-gradient-to-r from-[var(--teal)] to-[var(--t2)] shadow-[0_0_20px_rgba(14,165,199,.3)]"
          >
            ⚡ Lancer l&apos;uniquification ({files.length} fichier{files.length > 1 ? "s" : ""})
          </Button>
        </div>
      </div>
    );
  }

  if (step === "processing" && jobId) {
    return (
      <ProgressTracker
        jobId={jobId}
        onComplete={handleComplete}
        onCancel={() => setStep("results")}
      />
    );
  }

  if (step === "results" && jobId) {
    return (
      <ResultsGallery jobId={jobId} onReset={handleReset} />
    );
  }

  return null;
}
