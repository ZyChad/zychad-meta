"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch("/api/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.toLowerCase() }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Erreur");
        return;
      }
      setSent(true);
    } catch {
      setError("Une erreur est survenue.");
    } finally {
      setLoading(false);
    }
  }

  if (sent) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--zychad-bg)] p-4">
        <Card className="w-full max-w-md border-[var(--zychad-border)]">
          <CardHeader>
            <CardTitle className="text-[var(--zychad-teal-bright)]">Email envoyé</CardTitle>
            <CardDescription>
              Si un compte existe pour {email}, tu recevras un lien pour réinitialiser ton mot de passe.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/login">
              <Button variant="teal" className="w-full">Retour à la connexion</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--zychad-bg)] p-4">
      <Card className="w-full max-w-md border-[var(--zychad-border)]">
        <CardHeader>
          <CardTitle className="text-[var(--zychad-teal-bright)]">Mot de passe oublié</CardTitle>
          <CardDescription>Entre ton email pour recevoir un lien de réinitialisation</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <p className="text-sm text-[var(--zychad-red)] bg-[var(--zychad-red)]/10 p-3 rounded-md">{error}</p>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="toi@exemple.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="bg-[var(--zychad-bg)] border-[var(--zychad-border)]"
              />
            </div>
            <Button type="submit" className="w-full" variant="teal" disabled={loading}>
              {loading ? "Envoi..." : "Envoyer le lien"}
            </Button>
          </form>
          <p className="text-center text-sm text-[var(--zychad-dim)]">
            <Link href="/login" className="text-[var(--zychad-teal)] hover:underline">
              Retour à la connexion
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
