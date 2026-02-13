import { NextRequest } from "next/server";
import { getToken } from "next-auth/jwt";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });
  const userId = token?.sub;
  if (!userId) {
    return new Response("Unauthorized", { status: 401 });
  }

  const { id } = await params;
  const job = await prisma.job.findFirst({
    where: { id, userId },
  });
  if (!job) {
    return new Response("Not Found", { status: 404 });
  }

  const stream = new ReadableStream({
    async start(controller) {
      const send = (data: object) => {
        controller.enqueue(`data: ${JSON.stringify(data)}\n\n`);
      };

      const interval = setInterval(async () => {
        try {
          const j = await prisma.job.findFirst({
            where: { id, userId },
            select: { status: true, progress: true, total: true, currentFile: true, logs: true, error: true, outputZipKey: true },
          });
          if (!j) return;
          send({
            status: j.status,
            progress: j.progress,
            total: j.total,
            currentFile: j.currentFile,
            logs: j.logs,
            error: j.error,
            outputZipKey: j.outputZipKey,
          });
          if (j.status === "COMPLETED" || j.status === "FAILED" || j.status === "CANCELLED") {
            clearInterval(interval);
            controller.close();
          }
        } catch {
          clearInterval(interval);
          controller.close();
        }
      }, 1500);

      req.signal.addEventListener("abort", () => {
        clearInterval(interval);
        controller.close();
      });
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
