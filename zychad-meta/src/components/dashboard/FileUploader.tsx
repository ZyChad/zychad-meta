"use client";

import { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { validateFilename } from "@/lib/security";

const ALLOWED = {
  video: ["video/mp4", "video/quicktime", "video/x-msvideo", "video/webm", "video/x-matroska"],
  image: ["image/jpeg", "image/png", "image/webp"],
};
const EXTS = [".mp4", ".mov", ".avi", ".mkv", ".webm", ".jpg", ".jpeg", ".png", ".webp"];

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

export function FileUploader({
  onComplete,
  onQuotaBlocked,
  maxFileSize = 50 * 1024 * 1024,
}: {
  onComplete: (files: { name: string; s3Key: string; size: number; type: string }[], jobId: string) => void;
  onQuotaBlocked: (reason: string) => void;
  maxFileSize?: number;
}) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const validFile = (f: File): boolean => {
    const ext = "." + f.name.split(".").pop()?.toLowerCase();
    if (!EXTS.includes(ext)) return false;
    if (f.size > maxFileSize) return false;
    const v = validateFilename(f.name);
    return v.ok;
  };

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const items = Array.from(e.dataTransfer.files).filter(validFile);
    if (items.length === 0) {
      setError("Aucun fichier valide (mp4, mov, avi, mkv, webm, jpg, png, webp — max " + formatSize(maxFileSize) + ")");
      return;
    }
    await uploadFiles(items);
  }, [maxFileSize]);

  const handleSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const items = Array.from(e.target.files ?? []).filter(validFile);
    e.target.value = "";
    if (items.length === 0) return;
    await uploadFiles(items);
  }, [maxFileSize]);

  const uploadFiles = async (fileList: File[]) => {
    setError("");
    setUploading(true);
    try {
      const initRes = await fetch("/api/jobs/init", { method: "POST" });
      const initData = await initRes.json();
      if (!initRes.ok) {
        if (initData.shouldUpgrade) onQuotaBlocked(initData.error ?? "Quota atteint");
        else setError(initData.error ?? "Erreur");
        return;
      }
      const jobId = initData.jobId;

      const uploaded: { name: string; s3Key: string; size: number; type: string }[] = [];
      for (const file of fileList) {
        const presignRes = await fetch("/api/upload/presign", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            filename: file.name,
            contentType: file.type,
            jobId,
          }),
        });
        const presignData = await presignRes.json();
        if (!presignRes.ok) {
          if (presignData.shouldUpgrade) onQuotaBlocked(presignData.error ?? "Quota atteint");
          else setError(presignData.error ?? "Erreur presign");
          return;
        }
        await fetch(presignData.uploadUrl, {
          method: "PUT",
          body: file,
          headers: { "Content-Type": file.type },
        });
        uploaded.push({
          name: file.name,
          s3Key: presignData.key,
          size: file.size,
          type: file.type,
        });
      }
      onComplete(uploaded, jobId);
    } catch {
      setError("Erreur lors de l'upload");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div
        className={`rounded-xl border-2 border-dashed p-12 text-center transition-colors ${
          dragging
            ? "border-[var(--teal)] bg-[rgba(14,165,199,.08)]"
            : "border-[rgba(14,165,199,.3)] bg-[var(--s1)]"
        }`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
      >
        <input
          type="file"
          multiple
          accept={EXTS.join(",")}
          onChange={handleSelect}
          className="hidden"
          id="file-input"
        />
        <label htmlFor="file-input" className="cursor-pointer block">
          <p className="text-[var(--dim)] mb-2 text-lg">
            ⬆ Glisse tes fichiers ici
          </p>
          <p className="text-sm text-[var(--dim)] mb-2">ou clique pour sélectionner</p>
          <p className="text-sm text-[var(--mut)] mb-4">
            MP4, MOV, AVI, MKV, WebM, JPG, PNG, WebP
          </p>
          <p className="text-sm text-[var(--dim)] mb-4">Max {formatSize(maxFileSize)}</p>
          <Button
            variant="teal"
            disabled={uploading}
            onClick={(e) => { e.preventDefault(); document.getElementById("file-input")?.click(); }}
            className="rounded-[10px] bg-gradient-to-r from-[var(--teal)] to-[var(--t2)] shadow-[0_0_20px_rgba(14,165,199,.3)]"
          >
            {uploading ? "Upload en cours..." : "Sélectionner des fichiers"}
          </Button>
        </label>
      </div>
      {error && <p className="text-sm text-[var(--red)]">{error}</p>}
    </div>
  );
}
