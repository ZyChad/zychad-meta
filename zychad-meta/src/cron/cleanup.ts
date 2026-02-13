import { prisma } from "../lib/prisma";
import { deleteObject, listPrefix } from "../lib/s3";

async function main() {
  const expired = await prisma.job.findMany({
    where: { expiresAt: { lt: new Date() }, status: { in: ["COMPLETED", "FAILED"] } },
    select: { id: true, userId: true },
  });

  for (const job of expired) {
    const prefix = `jobs/${job.userId}/${job.id}/`;
    try {
      const keys = await listPrefix(prefix);
      for (const key of keys) {
        await deleteObject(key);
      }
    } catch {}
  }

  await prisma.job.updateMany({
    where: { expiresAt: { lt: new Date() }, status: { in: ["COMPLETED", "FAILED"] } },
    data: { status: "EXPIRED" },
  });

  console.log(`[cleanup] ${expired.length} jobs expirés traités`);
}

main()
  .then(() => process.exit(0))
  .catch((e) => {
    console.error(e);
    process.exit(1);
  });
