import { Resend } from "resend";

const resend = process.env.RESEND_API_KEY ? new Resend(process.env.RESEND_API_KEY) : null;

export async function sendVerificationEmail(email: string, token: string): Promise<boolean> {
  if (!resend) return false;
  const baseUrl = process.env.NEXTAUTH_URL ?? "https://zychadmeta.com";
  const verifyUrl = `${baseUrl}/verify-email?token=${encodeURIComponent(token)}`;
  try {
    const { error } = await resend.emails.send({
      from: process.env.EMAIL_FROM ?? "ZyChad Meta <noreply@zychadmeta.com>",
      to: email,
      subject: "Vérifie ton email — ZyChad Meta",
      html: `
        <p>Bienvenue sur ZyChad Meta !</p>
        <p>Clique sur le lien ci-dessous pour vérifier ton email :</p>
        <p><a href="${verifyUrl}">${verifyUrl}</a></p>
        <p>Ce lien expire dans 24 heures.</p>
        <p>Si tu n'as pas créé de compte, ignore cet email.</p>
      `,
    });
    return !error;
  } catch {
    return false;
  }
}
