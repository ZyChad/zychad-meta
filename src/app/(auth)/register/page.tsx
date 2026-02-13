"use client";

import { useState, useEffect } from "react";
import { signIn } from "next-auth/react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function RegisterPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const [googleEnabled, setGoogleEnabled] = useState(false);

  useEffect(() => {
    fetch("/api/auth/providers")
      .then((r) => r.json())
      .then((p) => setGoogleEnabled(!!p?.google))
      .catch(() => setGoogleEnabled(false));
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSuccess("");
    if (password.length < 8) {
      setError("Le mot de passe doit faire au moins 8 caractères.");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim() || undefined,
          email: email.toLowerCase(),
          password,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Erreur lors de l'inscription");
        return;
      }
      if (data.requiresVerification) {
        setSuccess(
          "Compte créé ! Vérifie ton email (et les spams) pour activer ton compte, puis connecte-toi."
        );
        return;
      }
      const signInRes = await signIn("credentials", {
        email: email.toLowerCase(),
        password,
        redirect: false,
        callbackUrl: "/dashboard",
      });
      // Full redirect pour que le cookie de session soit bien envoyé
      const target = signInRes?.url ?? "/dashboard";
      window.location.href = target;
    } catch {
      setError("Une erreur est survenue.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--zychad-bg)] p-4">
      <Card className="w-full max-w-md border-[var(--zychad-border)]">
        <CardHeader>
          <CardTitle className="text-[var(--zychad-teal-bright)]">Créer un compte</CardTitle>
          <CardDescription>3 uniquifications gratuites, sans carte</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <p className="text-sm text-[var(--zychad-red)] bg-[var(--zychad-red)]/10 p-3 rounded-md">
              {error}
            </p>
          )}
          {success && (
            <p className="text-sm text-[var(--zychad-teal)] bg-[var(--zychad-teal)]/10 p-3 rounded-md">
              {success}
            </p>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Nom (optionnel)</Label>
              <Input
                id="name"
                type="text"
                placeholder="Ton nom"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="bg-[var(--zychad-bg)] border-[var(--zychad-border)]"
              />
            </div>
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
            <div className="space-y-2">
              <Label htmlFor="password">Mot de passe (min. 8 caractères)</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                className="bg-[var(--zychad-bg)] border-[var(--zychad-border)]"
              />
            </div>
            <Button type="submit" className="w-full" variant="teal" disabled={loading}>
              {loading ? "Inscription..." : "S'inscrire"}
            </Button>
          </form>
          {googleEnabled && (
            <>
              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t border-[var(--zychad-border)]" />
                </div>
                <span className="relative flex justify-center text-xs text-[var(--zychad-dim)]">Ou</span>
              </div>
              <Button
                type="button"
                variant="outline"
                className="w-full border-[var(--zychad-border)]"
                onClick={() => signIn("google", { callbackUrl: "/dashboard" })}
              >
                Continuer avec Google
              </Button>
            </>
          )}
          <p className="text-center text-sm text-[var(--zychad-dim)]">
            Déjà un compte ?{" "}
            <Link href="/login" className="text-[var(--zychad-teal)] hover:underline">
              Se connecter
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
