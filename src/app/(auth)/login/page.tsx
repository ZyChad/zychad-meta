"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function LoginPage() {
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("redirect") || "/app/";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

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
