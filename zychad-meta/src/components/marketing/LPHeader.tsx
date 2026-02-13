"use client";

import Link from "next/link";
import { useSession } from "next-auth/react";
import { useEffect } from "react";
import { LOGO_DATA_URL } from "@/lib/brand";

export function LPHeader() {
  const { data: session, status } = useSession();

  useEffect(() => {
    const saved = localStorage.getItem("zt");
    if (saved === "l") {
      document.documentElement.classList.add("light");
      const sun = document.getElementById("ico-sun");
      const moon = document.getElementById("ico-moon");
      if (sun) sun.style.display = "block";
      if (moon) moon.style.display = "none";
    }
  }, []);

  const toggleTheme = () => {
    const html = document.documentElement;
    const isLight = html.classList.toggle("light");
    const sun = document.getElementById("ico-sun");
    const moon = document.getElementById("ico-moon");
    if (sun) sun.style.display = isLight ? "block" : "none";
    if (moon) moon.style.display = isLight ? "none" : "block";
    localStorage.setItem("zt", isLight ? "l" : "d");
  };

  return (
    <nav className="lp-nav">
      <Link href="/" className="n-logo">
        <img src={LOGO_DATA_URL} alt="ZyChad Meta" className="w-[30px] h-[30px] rounded-[9px] flex-shrink-0" />
        <span className="text-[var(--t2)]">ZyChad Meta</span>
      </Link>
      <div className="n-links">
        <Link href="#features">Features</Link>
        <Link href="#modes">Modes</Link>
        <Link href="#pricing">Tarifs</Link>
        <Link href="#comparison">Comparer</Link>
      </div>
      <div className="n-right">
        <button
          type="button"
          className="n-theme"
          onClick={toggleTheme}
          title="Changer le thème"
          aria-label="Changer le thème"
        >
          <svg id="ico-moon" viewBox="0 0 20 20" fill="none">
            <path
              d="M17 11a7 7 0 01-9.9-6.5A7 7 0 1017 11z"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinejoin="round"
            />
          </svg>
          <svg id="ico-sun" viewBox="0 0 20 20" fill="none" style={{ display: "none" }}>
            <circle cx="10" cy="10" r="4" stroke="currentColor" strokeWidth="1.5" />
            <path
              d="M10 2v2M10 16v2M2 10h2M16 10h2M4.93 4.93l1.41 1.41M13.66 13.66l1.41 1.41M4.93 15.07l1.41-1.41M13.66 6.34l1.41-1.41"
              stroke="currentColor"
              strokeWidth="1.3"
              strokeLinecap="round"
            />
          </svg>
        </button>
        <Link
          href={status === "loading" ? "#" : session ? "/app/" : "/register"}
          className="n-cta"
        >
          Commencer gratuitement
        </Link>
      </div>
    </nav>
  );
}
