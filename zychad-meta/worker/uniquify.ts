import { prisma } from "../src/lib/prisma";
import { s3, bucket, getOutputKey } from "../src/lib/s3";
import { GetObjectCommand, PutObjectCommand } from "@aws-sdk/client-s3";
import { createWriteStream, createReadStream, existsSync, mkdirSync, readdirSync } from "fs";
import { tmpdir } from "os";
import { join } from "path";
import { createInterface } from "readline";
import { spawn } from "child_process";
import archiver from "archiver";

const PROCESSING_DIR = join(process.cwd(), "processing");
const VIDEO_SCRIPT = join(PROCESSING_DIR, "uniquify_video.py");
const IMAGE_SCRIPT = join(PROCESSING_DIR, "uniquify_image.py");

type UniquifyJobData = {
  jobId: string;
  userId: string;
  inputFiles: { name: string; s3Key: string; size: number; type: string }[];
  variants: number;
  mode: string;
};

function isVideo(type: string): boolean {
  return /video\//.test(type) || /\.(mp4|mov|avi|mkv|webm)$/i.test(type);
}

async function downloadFromS3(s3Key: string, destPath: string): Promise<void> {
  const res = await s3.send(new GetObjectCommand({ Bucket: bucket, Key: s3Key }));
  const stream = res.Body as NodeJS.ReadableStream;
  const out = createWriteStream(destPath);
  await new Promise((resolve, reject) => {
    stream.pipe(out);
    out.on("finish", () => resolve(undefined));
    out.on("error", reject);
  });
}

async function runPython(script: string, args: string[]): Promise<void> {
  return new Promise((resolve, reject) => {
    const proc = spawn("python3", [script, ...args], {
      cwd: PROCESSING_DIR,
      stdio: ["ignore", "pipe", "pipe"],
    });
    let stderr = "";
    proc.stderr?.on("data", (d) => { stderr += d.toString(); });
    proc.on("close", (code) => {
      if (code === 0) resolve();
      else reject(new Error(stderr || `Exit ${code}`));
    });
  });
}

async function uploadToS3(localPath: string, s3Key: string, contentType: string): Promise<void> {
  const stream = createReadStream(localPath);
  await s3.send(
    new PutObjectCommand({
      Bucket: bucket,
      Key: s3Key,
      Body: stream,
      ContentType: contentType,
    })
  );
}

export async function processUniquifyJob(data: UniquifyJobData): Promise<void> {
  const { jobId, userId, inputFiles, variants, mode } = data;
  const workDir = join(tmpdir(), `zychad_${jobId}`);
  const inputDir = join(workDir, "input");
  const outputDir = join(workDir, "output");
  mkdirSync(inputDir, { recursive: true });
  mkdirSync(outputDir, { recursive: true });

  try {
    await prisma.job.update({
      where: { id: jobId },
      data: { status: "PROCESSING", startedAt: new Date(), progress: 0 },
    });

    let done = 0;
    const total = inputFiles.length * variants;
    const outputFiles: { name: string; s3Key: string; size: number }[] = [];

    for (let f = 0; f < inputFiles.length; f++) {
      const file = inputFiles[f];
      const localInput = join(inputDir, file.name);
      await downloadFromS3(file.s3Key, localInput);

      await prisma.job.update({
        where: { id: jobId },
        data: { currentFile: file.name },
      });

      const script = isVideo(file.type) ? VIDEO_SCRIPT : IMAGE_SCRIPT;
      if (!existsSync(script)) {
        throw new Error(`Script non trouvé: ${script}`);
      }

      for (let v = 0; v < variants; v++) {
        const ext = isVideo(file.type) ? ".mp4" : ".jpg";
        const baseName = file.name.replace(/\.[^.]+$/, "");
        const outName = `${baseName}_v${v + 1}${ext}`;
        const localOutput = join(outputDir, outName);

        if (isVideo(file.type)) {
          await runPython(VIDEO_SCRIPT, [
            localInput,
            localOutput,
            String(v),
            mode === "stealth" ? "1" : "0",
            mode === "double" ? "1" : "0",
          ]);
        } else {
          await runPython(IMAGE_SCRIPT, [
            localInput,
            localOutput,
            String(v),
            mode === "stealth" ? "1" : "0",
            mode === "double" ? "1" : "0",
          ]);
        }

        if (existsSync(localOutput)) {
          const s3Key = getOutputKey(userId, jobId, outName);
          const contentType = isVideo(file.type) ? "video/mp4" : "image/jpeg";
          await uploadToS3(localOutput, s3Key, contentType);
          const stat = await import("fs/promises").then((fs) => fs.stat(localOutput));
          outputFiles.push({ name: outName, s3Key, size: stat.size });
        }

        done++;
        await prisma.job.update({
          where: { id: jobId },
          data: { progress: done, logs: [{ t: new Date().toISOString(), m: `${file.name} → ${outName}`, l: "info" }] },
        });
      }
    }

    const zipName = `job_${jobId}.zip`;
    const zipPath = join(workDir, zipName);
    await new Promise<void>((resolve, reject) => {
      const archive = archiver("zip", { zlib: { level: 9 } });
      const out = createWriteStream(zipPath);
      archive.pipe(out);
      for (const f of readdirSync(outputDir)) {
        archive.file(join(outputDir, f), { name: f });
      }
      archive.finalize();
      out.on("close", () => resolve());
      archive.on("error", reject);
    });

    const zipS3Key = getOutputKey(userId, jobId, zipName);
    await uploadToS3(zipPath, zipS3Key, "application/zip");
    const zipStat = await import("fs/promises").then((fs) => fs.stat(zipPath));

    await prisma.job.update({
      where: { id: jobId },
      data: {
        status: "COMPLETED",
        progress: total,
        outputFiles,
        outputZipKey: zipS3Key,
        completedAt: new Date(),
      },
    });

    await prisma.user.update({
      where: { id: userId },
      data: {
        filesProcessedTotal: { increment: inputFiles.length },
        filesProcessedThisMonth: { increment: inputFiles.length },
      },
    });
  } catch (err) {
    await prisma.job.update({
      where: { id: jobId },
      data: {
        status: "FAILED",
        error: err instanceof Error ? err.message : String(err),
        completedAt: new Date(),
      },
    });
    throw err;
  } finally {
    await import("fs/promises").then((fs) => fs.rm(workDir, { recursive: true }).catch(() => {}));
  }
}
