"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

export default function SettingsPage() {
  const [apiKey, setApiKey] = useState<string | null>(null);

  const handleRegenerate = async () => {
    if (!confirm("Régénérer la clé API ? L'ancienne ne fonctionnera plus.")) return;
    const res = await fetch("/api/settings/api-key", { method: "POST" });
    const data = await res.json();
    if (data.key) setApiKey(data.key);
  };

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-[var(--zychad-text)] mb-6">Paramètres</h1>
      <div className="max-w-md space-y-6">
        <div className="space-y-2">
          <Label>Clé API</Label>
          <p className="text-sm text-[var(--zychad-dim)]">
            Utilise ta clé API pour les requêtes automatisées. Ne la partage jamais.
          </p>
          <Button variant="outline" onClick={handleRegenerate}>
            Régénérer la clé
          </Button>
          {apiKey && (
            <p className="text-sm font-mono text-[var(--zychad-teal)] break-all mt-2">
              Nouvelle clé : {apiKey}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
