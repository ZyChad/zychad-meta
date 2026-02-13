import { redirect } from "next/navigation";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { SettingsClient } from "./SettingsClient";

export default async function SettingsPage() {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    redirect("/login?redirect=/settings");
  }

  return (
    <div className="min-h-screen bg-[var(--zychad-bg)] p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold text-[var(--zychad-text)] mb-6">Paramètres</h1>
        <SettingsClient />
      </div>
    </div>
  );
}
