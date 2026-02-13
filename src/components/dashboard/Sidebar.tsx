"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { signOut } from "next-auth/react";
import {
  LayoutDashboard,
  Zap,
  Scissors,
  History,
  Settings,
  CreditCard,
  LogOut,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/uniquify", label: "Uniquifier", icon: Zap },
  { href: "/dashboard/scraper", label: "Scraper", icon: Scissors },
  { href: "/dashboard/history", label: "Historique", icon: History },
  { href: "/dashboard/billing", label: "Facturation", icon: CreditCard },
  { href: "/dashboard/settings", label: "Paramètres", icon: Settings },
];

export function Sidebar({ plan, userImage, userName }: { plan: string; userImage?: string | null; userName?: string | null }) {
  const pathname = usePathname();

  return (
    <aside className="w-56 border-r border-[var(--zychad-border)] bg-[var(--zychad-surface)] min-h-screen flex flex-col">
      <div className="p-4 border-b border-[var(--zychad-border)]">
        <Link href="/dashboard" className="text-lg font-bold text-[var(--zychad-teal-bright)] flex items-center gap-2">
          ⚡ ZyChad Meta
        </Link>
        <span className="inline-block mt-2 text-xs px-2 py-0.5 rounded bg-[var(--zychad-border)] text-[var(--zychad-dim)]">
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
                  ? "bg-[var(--zychad-teal)]/20 text-[var(--zychad-teal-bright)]"
                  : "text-[var(--zychad-dim)] hover:bg-[var(--zychad-border)]/50 hover:text-[var(--zychad-text)]"
              )}
            >
              <Icon className="w-4 h-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-[var(--zychad-border)] flex items-center gap-3">
        {userImage ? (
          <img src={userImage} alt="" className="w-8 h-8 rounded-full" />
        ) : (
          <div className="w-8 h-8 rounded-full bg-[var(--zychad-teal)]/30 flex items-center justify-center text-sm font-medium text-[var(--zychad-teal-bright)]">
            {(userName ?? "U").charAt(0).toUpperCase()}
          </div>
        )}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-[var(--zychad-text)] truncate">{userName ?? "Compte"}</p>
          <Button
            variant="ghost"
            size="sm"
            className="text-xs text-[var(--zychad-dim)] h-auto p-0 hover:text-[var(--zychad-red)]"
            onClick={() => signOut({ callbackUrl: "/" })}
          >
            <LogOut className="w-3 h-3 mr-1 inline" /> Déconnexion
          </Button>
        </div>
      </div>
    </aside>
  );
}
