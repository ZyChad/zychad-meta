"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
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
      const signInRes = await signIn("credentials", {
        email: email.toLowerCase(),
        password,
        redirect: false,
      });
      if (signInRes?.url) router.push(signInRes.url);
      else router.push("/app/");
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
            onClick={() => signIn("google", { callbackUrl: "/app/" })}
          >
            Continuer avec Google
          </Button>
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
