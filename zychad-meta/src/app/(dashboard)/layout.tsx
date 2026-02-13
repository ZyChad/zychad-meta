import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { Sidebar } from "@/components/dashboard/Sidebar";
import { SessionProvider } from "@/components/providers/SessionProvider";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await getServerSession(authOptions);
  if (!session?.user) redirect("/login");

  const userId = (session.user as { id?: string }).id;
  const dbUser = userId ? await prisma.user.findUnique({
    where: { id: userId },
    select: { plan: true, image: true, name: true },
  }) : null;

  const user = session.user as { id?: string; image?: string | null; name?: string | null; email?: string | null };
  const plan = dbUser?.plan ?? "FREE";

  return (
    <SessionProvider>
      <div className="flex min-h-screen bg-[var(--zychad-bg)]">
        <Sidebar
          plan={plan}
          userImage={dbUser?.image ?? user.image}
          userName={dbUser?.name ?? user.name ?? user.email ?? null}
          botUrl={process.env.BOT_URL ?? process.env.NEXT_PUBLIC_BOT_URL}
        />
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </SessionProvider>
  );
}
