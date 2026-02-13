"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { signOut } from "next-auth/react";
import {
  LayoutDashboard,
  Bot,
  Settings,
  CreditCard,
  LogOut,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// v2 - Uniquifier/Scraper/Historique retirés, Accéder au bot ajouté
const NAV = [
  { href: "/dashboard", label: "Accueil", icon: LayoutDashboard },
  { href: "/dashboard/billing", label: "Facturation", icon: CreditCard },
  { href: "/dashboard/settings", label: "Paramètres", icon: Settings },
];

export function Sidebar({
  plan,
  userImage,
  userName,
  botUrl,
}: {
  plan: string;
  userImage?: string | null;
  userName?: string | null;
  botUrl?: string | null;
}) {
  const pathname = usePathname();

  return (
    <aside className="w-56 border-r border-[var(--br)] bg-[var(--s1)] min-h-screen flex flex-col">
      <div className="p-5 border-b border-[var(--br)]">
        <Link href="/dashboard" className="text-lg font-bold text-[var(--zychad-teal-bright)] flex items-center gap-2 hover:opacity-90 transition">
          <span className="text-xl">⚡</span> ZyChad Meta
        </Link>
        <span className="inline-block mt-3 text-xs px-2.5 py-1 rounded-md bg-[rgba(14,165,199,.06)] text-[var(--zychad-teal-bright)] border border-[rgba(14,165,199,.15)]">
          {plan}
        </span>
      </div>
      <nav className="flex-1 p-2 space-y-1">
        {NAV.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
                active
                  ? "bg-[var(--s3)] text-[var(--zychad-teal-bright)]"
                  : "text-[var(--zychad-dim)] hover:bg-[rgba(255,255,255,.04)] hover:text-[var(--zychad-text)]"
              )}
            >
              <Icon className="w-4 h-4" />
              {item.label}
            </Link>
          );
        })}
        <a
          href={botUrl || "/app/"}
          target="_blank"
          rel="noopener noreferrer"
          className={cn(
            "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors mt-2",
            "bg-[rgba(14,165,199,.06)] border border-[rgba(14,165,199,.15)]",
            "text-[var(--zychad-teal-bright)] hover:bg-[rgba(14,165,199,.1)] hover:border-[rgba(14,165,199,.25)]"
          )}
        >
          <Bot className="w-4 h-4" />
          Accéder au bot
        </a>
      </nav>
      <div className="p-4 border-t border-[var(--br)] flex items-center gap-3">
        {userImage ? (
          <img src={userImage} alt="" className="w-9 h-9 rounded-xl object-cover" />
        ) : (
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[var(--zychad-teal)]/30 to-[var(--zychad-teal)]/10 flex items-center justify-center text-sm font-semibold text-[var(--zychad-teal-bright)]">
            {(userName ?? "U").charAt(0).toUpperCase()}
          </div>
        )}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-[var(--zychad-text)] truncate">{userName ?? "Compte"}</p>
          <Button
            variant="ghost"
            size="sm"
            className="text-xs text-[var(--zychad-dim)] h-auto p-0 hover:text-[var(--zychad-red)] transition"
            onClick={() => signOut({ callbackUrl: "/" })}
          >
            <LogOut className="w-3 h-3 mr-1 inline" /> Déconnexion
          </Button>
        </div>
      </div>
    </aside>
  );
}
