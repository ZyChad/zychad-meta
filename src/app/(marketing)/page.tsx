import { SessionProvider } from "@/components/providers/SessionProvider";
import { LPHeader } from "@/components/marketing/LPHeader";
import { LPContent } from "@/components/marketing/LPContent";

export default function HomePage() {
  return (
    <SessionProvider>
      <LPHeader />
      <LPContent />
    </SessionProvider>
  );
}
