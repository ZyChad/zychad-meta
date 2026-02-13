"use client";

import { useState, Suspense, useEffect } from "react";
import { signIn } from "next-auth/react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

function LoginForm() {
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("redirect") || "/dashboard";
  const verified = searchParams.get("verified") === "1";
  const errorParam = searchParams.get("error");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [googleEnabled, setGoogleEnabled] = useState(false);

  useEffect(() => {
    fetch("/api/auth/providers")
      .then((r) => r.json())
      .then((p) => setGoogleEnabled(!!p?.google))
      .catch(() => setGoogleEnabled(false));
    if (errorParam === "token_invalid") setError("Lien de vérification invalide ou expiré.");
    if (errorParam === "token_missing") setError("Lien de vérification manquant.");
  }, [errorParam]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await signIn("credentials", {
        email: email.toLowerCase(),
        password,
        redirect: false,
        callbackUrl,
      });
      if (res?.error) {
        setError(res.error);
        return;
      }
      // Full redirect pour que le cookie de session soit bien envoyé
      window.location.href = res?.url ?? callbackUrl;
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
          <CardTitle className="text-[var(--zychad-teal-bright)]">Connexion</CardTitle>
          <CardDescription>Accède à ton compte ZyChad Meta</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {verified && (
            <p className="text-sm text-[var(--zychad-teal)] bg-[var(--zychad-teal)]/10 p-3 rounded-md">
              Email vérifié ! Tu peux te connecter.
            </p>
          )}
          {error && (
            <p className="text-sm text-[var(--zychad-red)] bg-[var(--zychad-red)]/10 p-3 rounded-md">
              {error}
            </p>
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
            <div className="space-y-2">
              <Label htmlFor="password">Mot de passe</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="bg-[var(--zychad-bg)] border-[var(--zychad-border)]"
              />
            </div>
            <div className="flex justify-end">
              <Link href="/forgot-password" className="text-sm text-[var(--zychad-teal)] hover:underline">
                Mot de passe oublié ?
              </Link>
            </div>
            <Button type="submit" className="w-full" variant="teal" disabled={loading}>
              {loading ? "Connexion..." : "Se connecter"}
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
                onClick={() => signIn("google", { callbackUrl })}
              >
                Continuer avec Google
              </Button>
            </>
          )}
          <p className="text-center text-sm text-[var(--zychad-dim)]">
            Pas encore de compte ?{" "}
            <Link href="/register" className="text-[var(--zychad-teal)] hover:underline">
              S&apos;inscrire
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-[var(--zychad-bg)]">
        <div className="animate-pulse text-[var(--zychad-dim)]">Chargement...</div>
      </div>
    }>
      <LoginForm />
    </Suspense>
  );
}
