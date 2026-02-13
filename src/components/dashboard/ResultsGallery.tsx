"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";

export function ResultsGallery({
  jobId,
  onReset,
}: {
  jobId: string;
  onReset: () => void;
}) {
  const [job, setJob] = useState<{
    status: string;
    outputZipKey?: string | null;
    outputFiles?: { name: string; s3Key: string }[];
  } | null>(null);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/jobs/${jobId}`)
      .then((r) => r.json())
      .then(setJob);
  }, [jobId]);

  const handleDownload = async () => {
    if (!job?.outputZipKey) return;
    const res = await fetch(`/api/jobs/${jobId}/download`);
    const data = await res.json();
    if (data.url) {
      setDownloadUrl(data.url);
      window.open(data.url, "_blank");
    }
  };

  if (!job) return <p className="text-[var(--dim)]">Chargement...</p>;

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="rounded-xl border border-[rgba(20,51,69,.4)] bg-[var(--s1)] p-6">
        <h2 className="text-lg font-semibold text-[var(--txt)] mb-4">Résultats</h2>
        {job.status === "COMPLETED" && (
          <>
            {job.outputFiles && job.outputFiles.length > 0 && (
              <p className="text-sm text-[var(--dim)] mb-4">
                {job.outputFiles.length} fichier(s) généré(s)
              </p>
            )}
            {job.outputZipKey && (
              <Button
                variant="teal"
                onClick={handleDownload}
                className="rounded-[10px] mb-4 bg-gradient-to-r from-[var(--teal)] to-[var(--t2)] shadow-[0_0_20px_rgba(14,165,199,.3)]"
              >
                Télécharger tout (.zip)
              </Button>
            )}
          </>
        )}
        {job.status === "FAILED" && (
          <p className="text-sm text-[var(--red)]">Le traitement a échoué.</p>
        )}
        <Button variant="outline" onClick={onReset} className="rounded-[10px]">
          Nouvelle uniquification
        </Button>
      </div>
    </div>
  );
}
