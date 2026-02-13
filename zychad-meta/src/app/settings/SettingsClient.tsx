"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function SettingsClient() {
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handleUpdateName = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");
    try {
      const res = await fetch("/api/settings/profile", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      const data = await res.json();
      if (res.ok) setMessage("Profil mis à jour");
      else setMessage(data.error ?? "Erreur");
    } catch {
      setMessage("Erreur");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <form onSubmit={handleUpdateName} className="space-y-4">
        <div className="space-y-2">
          <Label>Nom</Label>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Ton nom"
            className="bg-[var(--s2)] border-[var(--s3)] rounded-[10px] max-w-md"
          />
        </div>
        <Button type="submit" variant="teal" disabled={loading} className="rounded-[10px]">
          {loading ? "Enregistrement..." : "Mettre à jour"}
        </Button>
        {message && <p className="text-sm text-[var(--dim)]">{message}</p>}
      </form>

      <p className="text-sm text-[var(--dim)]">
        <Link href="/app/" className="text-[var(--teal)] hover:underline">
          ← Retour à l&apos;app
        </Link>
      </p>
    </div>
  );
}
