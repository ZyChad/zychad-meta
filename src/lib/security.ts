import { z } from "zod";

const ALLOWED_MIME = [
  "video/mp4",
  "video/quicktime",
  "video/x-msvideo",
  "video/webm",
  "video/x-matroska",
  "image/jpeg",
  "image/png",
  "image/webp",
] as const;

const ALLOWED_EXT = [".mp4", ".mov", ".avi", ".mkv", ".webm", ".jpg", ".jpeg", ".png", ".webp"] as const;

const SAFE_FILENAME = /^[a-zA-Z0-9._-]{1,200}$/;

export function sanitizeFilename(name: string): string {
  const base = name.replace(/[^a-zA-Z0-9._-]/g, "_").slice(0, 200);
  return base || "file";
}

export function isAllowedExtension(filename: string): boolean {
  const ext = filename.slice(filename.lastIndexOf(".")).toLowerCase();
  return (ALLOWED_EXT as readonly string[]).includes(ext);
}

export function isAllowedMime(mime: string): boolean {
  return (ALLOWED_MIME as readonly string[]).includes(mime);
}

export function validateFilename(filename: string): { ok: boolean; error?: string } {
  if (!filename || filename.length > 200) return { ok: false, error: "Nom de fichier invalide" };
  if (!SAFE_FILENAME.test(filename)) return { ok: false, error: "Caractères non autorisés" };
  if (!isAllowedExtension(filename)) return { ok: false, error: "Extension non autorisée" };
  return { ok: true };
}

export const createJobSchema = z.object({
  files: z.array(
    z.object({
      name: z.string().max(200),
      s3Key: z.string().min(1).max(500),
      size: z.number().int().min(1),
      type: z.string(),
    })
  ).min(1).max(50),
  variants: z.number().int().min(1).max(100),
  mode: z.enum(["normal", "double", "stealth"]),
});

export type CreateJobInput = z.infer<typeof createJobSchema>;
