import {
  S3Client,
  PutObjectCommand,
  GetObjectCommand,
  DeleteObjectCommand,
  ListObjectsV2Command,
} from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";

const endpoint = process.env.S3_ENDPOINT;
const region = process.env.S3_REGION ?? "us-east-1";
const bucket = process.env.S3_BUCKET ?? "zychad-files";
const forcePathStyle = !!endpoint && endpoint.includes("minio");

export const s3 = new S3Client({
  region,
  ...(endpoint
    ? {
        endpoint,
        forcePathStyle,
        credentials: {
          accessKeyId: process.env.S3_ACCESS_KEY ?? "",
          secretAccessKey: process.env.S3_SECRET_KEY ?? "",
        },
      }
    : {}),
});

export function getUploadKey(userId: string, jobId: string, filename: string): string {
  const safe = filename.replace(/[^a-zA-Z0-9._-]/g, "_").slice(0, 150);
  return `jobs/${userId}/${jobId}/input/${Date.now()}_${safe}`;
}

export function getOutputKey(userId: string, jobId: string, filename: string): string {
  const safe = filename.replace(/[^a-zA-Z0-9._-]/g, "_").slice(0, 150);
  return `jobs/${userId}/${jobId}/output/${safe}`;
}

export async function presignUpload(key: string, contentType: string, expiresIn = 900): Promise<string> {
  const cmd = new PutObjectCommand({
    Bucket: bucket,
    Key: key,
    ContentType: contentType,
  });
  return getSignedUrl(s3, cmd, { expiresIn });
}

export async function presignDownload(key: string, expiresIn = 3600): Promise<string> {
  const cmd = new GetObjectCommand({ Bucket: bucket, Key: key });
  return getSignedUrl(s3, cmd, { expiresIn });
}

export async function deleteObject(key: string): Promise<void> {
  await s3.send(new DeleteObjectCommand({ Bucket: bucket, Key: key }));
}

export async function listPrefix(prefix: string): Promise<string[]> {
  const list = await s3.send(
    new ListObjectsV2Command({ Bucket: bucket, Prefix: prefix })
  );
  return (list.Contents ?? []).map((c) => c.Key!).filter(Boolean);
}

export { bucket };
