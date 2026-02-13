import { NextAuthOptions } from "next-auth";
import { PrismaAdapter } from "@auth/prisma-adapter";
import CredentialsProvider from "next-auth/providers/credentials";
import GoogleProvider from "next-auth/providers/google";
import bcrypt from "bcryptjs";
import { prisma } from "./prisma";

const MAX_FAILED_ATTEMPTS = 5;
const LOCK_DURATION_MS = 15 * 60 * 1000;

const isProd = process.env.NODE_ENV === "production";
const baseUrl = process.env.NEXTAUTH_URL ?? "";

export const authOptions: NextAuthOptions = {
  adapter: PrismaAdapter(prisma) as NextAuthOptions["adapter"],
  session: { strategy: "jwt", maxAge: 24 * 60 * 60 },
  pages: { signIn: "/login" },
  cookies: isProd && baseUrl.includes("zychadmeta.com")
    ? {
        sessionToken: {
          name: "__Secure-next-auth.session-token",
          options: {
            httpOnly: true,
            sameSite: "lax",
            path: "/",
            secure: true,
            domain: ".zychadmeta.com",
          },
        },
      }
    : undefined,
  providers: [
    ...(process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET
      ? [
          GoogleProvider({
            clientId: process.env.GOOGLE_CLIENT_ID,
            clientSecret: process.env.GOOGLE_CLIENT_SECRET,
          }),
        ]
      : []),
    CredentialsProvider({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Mot de passe", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null;

        const user = await prisma.user.findUnique({
          where: { email: credentials.email.toLowerCase() },
        });
        if (!user?.passwordHash) return null;

        // Vérification email requise si un token a été envoyé
        if (user.emailVerificationToken && !user.emailVerified) {
          throw new Error("Vérifie ton email avant de te connecter. Regarde ta boîte de réception.");
        }

        if (user.lockedUntil && new Date(user.lockedUntil) > new Date()) {
          throw new Error("Compte temporairement verrouillé. Réessaie dans 15 minutes.");
        }

        const ok = await bcrypt.compare(credentials.password, user.passwordHash);
        if (!ok) {
          const attempts = (user.failedLoginAttempts ?? 0) + 1;
          await prisma.user.update({
            where: { id: user.id },
            data: {
              failedLoginAttempts: attempts,
              ...(attempts >= MAX_FAILED_ATTEMPTS
                ? { lockedUntil: new Date(Date.now() + LOCK_DURATION_MS) }
                : {}),
            },
          });
          throw new Error(attempts >= MAX_FAILED_ATTEMPTS ? "Compte verrouillé. Réessaie dans 15 min." : "Email ou mot de passe incorrect.");
        }

        await prisma.user.update({
          where: { id: user.id },
          data: {
            failedLoginAttempts: 0,
            lockedUntil: null,
            lastLoginAt: new Date(),
          },
        });

        return {
          id: user.id,
          email: user.email,
          name: user.name,
          image: user.image,
        };
      },
    }),
  ],
  callbacks: {
    async signIn({ user, account }) {
      if (account?.provider === "google" && user?.email) {
        await prisma.user.updateMany({
          where: { email: user.email },
          data: { emailVerified: new Date(), emailVerificationToken: null, emailVerificationExpires: null },
        });
      }
      return true;
    },
    async jwt({ token, user }) {
      if (user) {
        const uid = (user as { id?: string }).id ?? token.sub;
        token.id = uid;
        token.sub = uid; // pour getToken/jwt.sub
        token.email = user.email;
      } else if (token.sub && !token.id) {
        token.id = token.sub;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        (session.user as { id: string }).id = token.id as string;
      }
      return session;
    },
  },
};
