"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function HistoryPage() {
  const [jobs, setJobs] = useState<{ id: string; status: string; createdAt: string }[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    fetch(`/api/jobs?page=${page}&limit=20`)
      .then((r) => r.json())
      .then((d) => {
        setJobs(d.jobs ?? []);
        setTotal(d.total ?? 0);
      });
  }, [page]);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-[var(--zychad-text)] mb-6">Historique</h1>
      <div className="rounded-lg border border-[var(--zychad-border)] overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--zychad-border)] bg-[var(--zychad-surface)]">
              <th className="text-left p-4 text-[var(--zychad-dim)]">ID</th>
              <th className="text-left p-4 text-[var(--zychad-dim)]">Statut</th>
              <th className="text-left p-4 text-[var(--zychad-dim)]">Date</th>
              <th className="text-left p-4 text-[var(--zychad-dim)]"></th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((j) => (
              <tr key={j.id} className="border-b border-[var(--zychad-border)]">
                <td className="p-4 text-[var(--zychad-text)] font-mono text-xs">{j.id.slice(0, 12)}…</td>
                <td className="p-4 text-[var(--zychad-text)]">{j.status}</td>
                <td className="p-4 text-[var(--zychad-dim)]">
                  {new Date(j.createdAt).toLocaleDateString("fr-FR")}
                </td>
                <td className="p-4">
                  <Link href={`/dashboard/history?job=${j.id}`}>
                    <Button variant="ghost" size="sm">Voir</Button>
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {total > 20 && (
        <div className="flex justify-center gap-2 mt-4">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Précédent
          </Button>
          <Button variant="outline" size="sm" disabled={page * 20 >= total} onClick={() => setPage((p) => p + 1)}>
            Suivant
          </Button>
        </div>
      )}
    </div>
  );
}
