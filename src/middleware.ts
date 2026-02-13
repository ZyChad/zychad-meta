import { getToken } from "next-auth/jwt";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = ["/", "/login", "/register", "/forgot-password", "/pricing"];
const AUTH_PATHS = ["/login", "/register", "/forgot-password"];
const API_AUTH_EXCEPTIONS = ["/api/auth/", "/api/paddle/webhook", "/api/webhooks/paddle", "/api/health", "/api/usage/increment"];
export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  if (process.env.NODE_ENV === "production") {
    const proto = req.headers.get("x-forwarded-proto");
    if (proto === "http") {
      const url = req.nextUrl.clone();
      url.protocol = "https:";
      return NextResponse.redirect(url, 301);
    }
  }

  const res = NextResponse.next();
  res.headers.set("X-Frame-Options", "DENY");
  res.headers.set("X-Content-Type-Options", "nosniff");
  res.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
  // CSP désactivé en dev pour éviter les blocages
  if (process.env.NODE_ENV === "production") {
    res.headers.set(
      "Content-Security-Policy",
      "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.paddle.com; frame-src https://cdn.paddle.com https://*.paddle.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https: blob:; connect-src 'self' https://api.paddle.com https://cdn.paddle.com; font-src 'self' data:;"
    );
  }
  res.headers.set("Strict-Transport-Security", "max-age=31536000; includeSubDomains");

  const isApi = pathname.startsWith("/api/");
  const isAuthException = API_AUTH_EXCEPTIONS.some((p) => pathname.startsWith(p));

  if (isApi) {
    if (isAuthException) return res;
    const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });
    const apiKey = req.headers.get("x-api-key");
    if (!token?.sub && !apiKey) {
      return NextResponse.json({ error: "Non autorisé" }, { status: 401 });
    }
    return res;
  }

  const isProtected = pathname.startsWith("/dashboard") || pathname.startsWith("/billing") || pathname.startsWith("/settings") || pathname.startsWith("/app");
  const isPublic = PUBLIC_PATHS.some((p) => p === pathname || (p !== "/" && pathname.startsWith(p)));

  if (isProtected) {
    const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });
    if (!token?.sub) {
      const login = new URL("/login", req.url);
      login.searchParams.set("redirect", pathname);
      return NextResponse.redirect(login);
    }
    return res;
  }

  if (AUTH_PATHS.some((p) => pathname.startsWith(p))) {
    const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });
    if (token?.sub) {
      return NextResponse.redirect(new URL("/dashboard", req.url));
    }
  }

  return res;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
