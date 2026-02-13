"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Image, Video } from "lucide-react";

type Platform = "ig" | "tt";

export default function ScraperPage() {
  const [platform, setPlatform] = useState<Platform>("ig");
  const [username, setUsername] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);
  const [filesFound, setFilesFound] = useState(0);
  const [filesDownloaded, setFilesDownloaded] = useState(0);

  const handleScrape = async () => {
    if (!username.trim()) return;
    setError("");
    setLoading(true);
    setJobId(null);
    try {
      const res = await fetch("/api/scraper", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ platform, username: username.replace("@", "").trim() }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Erreur");
        return;
      }
      setJobId(data.jobId);
    } catch {
      setError("Erreur");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-4xl">
      <h1 className="text-2xl font-bold text-[var(--txt)] mb-2">Scraper</h1>
      <p className="text-[var(--dim)] mb-8">Récupère les posts d&apos;un profil Instagram ou TikTok</p>

      <div className="space-y-6">
        <div className="rounded-xl border border-[rgba(20,51,69,.4)] bg-[var(--s1)] p-6">
          <div className="flex gap-2 mb-4">
            <button
              type="button"
              onClick={() => setPlatform("ig")}
              className={`flex items-center gap-2 px-4 py-2 rounded-[10px] font-medium transition-colors ${
                platform === "ig"
                  ? "bg-[var(--teal)] text-[var(--bg)]"
                  : "bg-[var(--s2)] text-[var(--dim)] hover:bg-[var(--s3)]"
              }`}
            >
              <Image className="w-4 h-4" />
              Instagram
            </button>
            <button
              type="button"
              onClick={() => setPlatform("tt")}
              className={`flex items-center gap-2 px-4 py-2 rounded-[10px] font-medium transition-colors ${
                platform === "tt"
                  ? "bg-[var(--teal)] text-[var(--bg)]"
                  : "bg-[var(--s2)] text-[var(--dim)] hover:bg-[var(--s3)]"
              }`}
            >
              <Video className="w-4 h-4" />
              TikTok
            </button>
          </div>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--dim)]">@</span>
              <Input
                placeholder="username_here"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="pl-8 bg-[var(--s2)] border-[var(--s3)] rounded-[10px] focus:border-[var(--teal)]"
              />
            </div>
            <Button
              variant="teal"
              onClick={handleScrape}
              disabled={loading}
              className="rounded-[10px] bg-gradient-to-r from-[var(--teal)] to-[var(--t2)] shadow-[0_0_20px_rgba(14,165,199,.3)]"
            >
              {loading ? "Scraping..." : "Scraper"}
            </Button>
          </div>
        </div>

        {error && <p className="text-sm text-[var(--red)]">{error}</p>}

        {jobId && (
          <div className="rounded-xl border border-[rgba(20,51,69,.4)] bg-[var(--s1)] p-6">
            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-4">
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((i) => (
                <div
                  key={i}
                  className="aspect-square rounded-lg bg-[var(--s2)] border border-[var(--s3)] flex items-center justify-center"
                >
                  {i % 2 === 0 ? (
                    <Video className="w-8 h-8 text-[var(--dim)]" />
                  ) : (
                    <Image className="w-8 h-8 text-[var(--dim)]" />
                  )}
                </div>
              ))}
              <div className="aspect-square rounded-lg bg-[var(--s2)] border border-dashed border-[var(--s3)] flex items-center justify-center text-[var(--dim)] text-sm">
                +{filesFound > 10 ? filesFound - 10 : "..."}
              </div>
            </div>
            <div className="mt-4 flex gap-6 text-sm text-[var(--dim)]">
              <span>{filesFound || 0} fichiers</span>
              <span>{filesDownloaded || 0} téléchargés</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
