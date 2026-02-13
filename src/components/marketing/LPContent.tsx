"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";

const TECHNIQUES_1 = [
  "📐 Pixel shift",
  "🔊 Pitch shift",
  "🎨 Hue ±2°",
  "🌊 Noise injection",
  "🎬 GOP",
  "📊 Bitrate",
  "✂️ Trim",
  "🔲 Chromatic",
  "🌑 Vignette",
  "📷 EXIF spoof",
  "🎭 Lens distortion",
  "💫 Gradient overlay",
  "🔄 Micro-rotation",
];

const TECHNIQUES_2 = [
  "🔧 EQ multi-band",
  "🎞️ FPS change",
  "🖼️ Letterbox",
  "⚡ Speed ±3%",
  "🎵 Phase invert",
  "🔍 Micro blur",
  "🎨 Gamma local",
  "🔉 Stereo width",
  "📱 Device spoof",
  "🎬 CRF",
  "🌫️ Grain overlay",
  "🔊 Micro reverb",
];

const PRICING_PLANS = [
  {
    name: "Starter",
    priceM: 29,
    priceY: 23,
    features: [
      "200 fichiers / mois",
      "10 variantes max",
      "Normal + Double Process",
      "Instagram Scraper",
      "Support email",
    ],
    popular: false,
  },
  {
    name: "Pro",
    priceM: 79,
    priceY: 63,
    features: [
      "1 000 fichiers / mois",
      "50 variantes max",
      "Mode Stealth inclus",
      "IG + TikTok Scraper",
      "Support prioritaire",
    ],
    popular: true,
  },
  {
    name: "Agency",
    priceM: 199,
    priceY: 159,
    features: [
      "Fichiers illimités",
      "100 variantes max",
      "Tous les modes",
      "Scraper illimité",
      "Support Telegram",
    ],
    popular: false,
  },
];

export function LPContent() {
  const { data: session } = useSession();
  const [yearly, setYearly] = useState(false);

  useEffect(() => {
    const obs = new IntersectionObserver(
      (e) => {
        e.forEach((el) => {
          if (el.isIntersecting) el.target.classList.add("vis");
        });
      },
      { threshold: 0.08, rootMargin: "0px 0px -40px 0px" }
    );
    document.querySelectorAll(".rv").forEach((el) => obs.observe(el));
  }, []);

  const ctaHref = session ? "/app/" : "/register";
  const billingHref = session ? "/billing" : "/register";

  return (
    <div className="lp-main">
      {/* Hero — v5 centered */}
      <section className="hero">
        <div className="lp-w">
          <div className="rv">
            <div className="h-badge">
              <span className="dot" /> 3 essais gratuits · Sans carte bancaire
            </div>
            <h1>
              Rends chaque contenu <span className="hl">unique. Automatiquement.</span>
            </h1>
            <p>
              25+ techniques invisibles pour contourner la détection de contenu dupliqué.
              Upload, uniquifie, poste.
            </p>
            <div className="h-actions">
              <Link href={ctaHref} className="btn btn-p">
                ⚡ Commencer gratuitement
              </Link>
              <Link href="#features" className="btn btn-s">
                Découvrir →
              </Link>
            </div>
            <div className="h-note">
              <span>✓ Aucune carte</span>
              <span>✓ 3 essais offerts</span>
              <span>✓ Setup 30s</span>
            </div>
          </div>
        </div>
        <div className="lp-w rv rv-d2">
          <div className="stats-bar">
            <div className="stat">
              <div className="stat-v" style={{ color: "var(--t3)" }}>
                25+
              </div>
              <div className="stat-l">Techniques</div>
            </div>
            <div className="stat">
              <div className="stat-v" style={{ color: "var(--gn)" }}>
                99.7%
              </div>
              <div className="stat-l">Taux d&apos;unicité</div>
            </div>
            <div className="stat">
              <div className="stat-v" style={{ color: "var(--t4)" }}>
                1.8s
              </div>
              <div className="stat-l">Temps moyen</div>
            </div>
            <div className="stat">
              <div className="stat-v" style={{ color: "var(--pr)" }}>
                500+
              </div>
              <div className="stat-l">Utilisateurs</div>
            </div>
          </div>
        </div>
      </section>

      {/* Product Showcase */}
      <section className="showcase rv">
        <div className="lp-w">
          <div className="mock">
            <div className="mock-bar">
              <div className="dot dr" />
              <div className="dot dy" />
              <div className="dot dg" />
              <div className="mock-url">app.zychadmeta.com/dashboard</div>
            </div>
            <div className="mock-body">
              <div className="mock-tabs">
                <div className="mtab on">⚡ Uniquifier</div>
                <div className="mtab">IG Scraper</div>
                <div className="mtab">TT Scraper</div>
                <div className="mtab">Historique</div>
              </div>
              <div className="mock-stats">
                <div className="ms">
                  <div className="ms-l">Fichiers traités</div>
                  <div className="ms-v" style={{ color: "var(--t3)" }}>
                    2,847
                  </div>
                  <div className="ms-s">+127 aujourd&apos;hui</div>
                </div>
                <div className="ms">
                  <div className="ms-l">Variantes générées</div>
                  <div className="ms-v" style={{ color: "var(--t4)" }}>
                    14,235
                  </div>
                  <div className="ms-s">×5 en moyenne</div>
                </div>
                <div className="ms">
                  <div className="ms-l">Taux unique</div>
                  <div className="ms-v" style={{ color: "var(--gn)" }}>
                    99.7%
                  </div>
                  <div className="ms-s">Safe to post</div>
                </div>
              </div>
              <div className="prog">
                <div className="prog-fill" />
              </div>
              <div className="frow">
                <svg viewBox="0 0 16 16">
                  <rect
                    x="2"
                    y="1"
                    width="12"
                    height="14"
                    rx="2"
                    fill="var(--s3)"
                    stroke="var(--t2)"
                    strokeWidth=".7"
                  />
                  <polygon
                    points="6,5 6,11 11,8"
                    fill="var(--t3)"
                    opacity=".6"
                  />
                </svg>
                <span className="nm">reel_model_001.mp4</span>
                <span className="bg b-ok">✓ 10 variantes</span>
              </div>
              <div className="frow">
                <svg viewBox="0 0 16 16">
                  <rect
                    x="2"
                    y="1"
                    width="12"
                    height="14"
                    rx="2"
                    fill="var(--s3)"
                    stroke="var(--t2)"
                    strokeWidth=".7"
                  />
                  <polygon
                    points="6,5 6,11 11,8"
                    fill="var(--t3)"
                    opacity=".6"
                  />
                </svg>
                <span className="nm">story_sofia_023.mp4</span>
                <span className="bg b-pr">⚡ En cours</span>
              </div>
              <div className="frow">
                <svg viewBox="0 0 16 16">
                  <rect
                    x="2"
                    y="1"
                    width="12"
                    height="14"
                    rx="2"
                    fill="var(--s3)"
                    stroke="var(--mt)"
                    strokeWidth=".5"
                  />
                  <rect
                    x="4"
                    y="4"
                    width="8"
                    height="6"
                    rx="1"
                    fill="var(--s4)"
                  />
                  <circle
                    cx="6.5"
                    cy="7"
                    r="1.2"
                    fill="var(--mt)"
                    opacity=".4"
                  />
                </svg>
                <span className="nm">carousel_003.jpg</span>
                <span style={{ fontSize: "8.5px", color: "var(--mt)" }}>
                  En attente
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Big Statement */}
      <div className="divider" />
      <section className="big rv">
        <div className="lp-w">
          <h2>
            Instagram et TikTok détectent <span className="hl">les contenus dupliqués.</span>
            <br />
            Shadowban. Zéro reach. Compte grillé.
          </h2>
          <p>
            ZyChad Meta modifie chaque fichier en profondeur — invisible à l&apos;œil,
            indétectable par les algorithmes.
          </p>
        </div>
      </section>
      <div className="divider" />

      {/* Feature 1: Uniquifier */}
      <section className="feat" id="features">
        <div className="lp-w">
          <div className="fg rv">
            <div className="ft">
              <div className="flabel">⚡ Uniquifier</div>
              <h2>
                Upload. Configure. <span className="hl">Uniquifie.</span>
              </h2>
              <p>
                Glisse tes fichiers, choisis le nombre de variantes et le mode. Chaque output
                est unique et passe tous les checks.
              </p>
              <div className="pills">
                <span className="pill">Drag & drop</span>
                <span className="pill">1–100 variantes</span>
                <span className="pill">Vidéo + Image</span>
                <span className="pill">Download .zip</span>
              </div>
              <Link href={ctaHref} className="btn btn-p">
                Essayer gratuitement
              </Link>
            </div>
            <div className="fv">
              <div className="fm">
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: 12,
                  }}
                >
                  <span
                    style={{
                      fontSize: 12,
                      fontWeight: 700,
                      color: "var(--t3)",
                    }}
                  >
                    ⚡ Traitement en cours
                  </span>
                  <span
                    style={{
                      fontSize: 11,
                      color: "var(--gn)",
                      fontWeight: 600,
                    }}
                  >
                    72%
                  </span>
                </div>
                <div className="prog" style={{ marginBottom: 16 }}>
                  <div
                    className="prog-fill"
                    style={{ width: "72%", animation: "none" }}
                  />
                </div>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: 10,
                  }}
                >
                  <div
                    style={{
                      background: "var(--s2)",
                      borderRadius: 8,
                      padding: 14,
                      textAlign: "center",
                    }}
                  >
                    <div
                      style={{
                        fontSize: 8,
                        color: "var(--mt)",
                        textTransform: "uppercase",
                        marginBottom: 5,
                      }}
                    >
                      Original
                    </div>
                    <svg
                      viewBox="0 0 40 48"
                      width={38}
                      height={44}
                      style={{ display: "block", margin: "0 auto 5px" }}
                    >
                      <rect
                        x="2"
                        y="2"
                        width="36"
                        height="44"
                        rx="4"
                        fill="var(--s3)"
                        stroke="var(--br)"
                        strokeWidth="1"
                      />
                      <polygon
                        points="15,16 15,34 28,25"
                        fill="var(--t3)"
                        opacity=".4"
                      />
                    </svg>
                    <div
                      style={{
                        fontFamily: "JetBrains Mono",
                        fontSize: 9,
                        color: "var(--dm)",
                      }}
                    >
                      reel.mp4
                    </div>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                    {["v1.mp4", "v2.mp4", "v3.mp4", "v4.mp4"].map((v, i) => (
                      <div
                        key={v}
                        style={{
                          background: "var(--s2)",
                          borderRadius: 6,
                          padding: "7px 10px",
                          display: "flex",
                          alignItems: "center",
                          gap: 7,
                        }}
                      >
                        <svg viewBox="0 0 14 14" width={14} height={14}>
                          <rect
                            x="1"
                            y="1"
                            width="12"
                            height="12"
                            rx="2"
                            fill="var(--s3)"
                            stroke="var(--br)"
                            strokeWidth=".5"
                          />
                          <polygon
                            points="5,4 5,10 10,7"
                            fill="var(--t3)"
                            opacity=".5"
                          />
                        </svg>
                        <span
                          style={{
                            fontFamily: "JetBrains Mono",
                            fontSize: 9,
                            color: "var(--dm)",
                            flex: 1,
                          }}
                        >
                          {v}
                        </span>
                        <span
                          style={{
                            fontSize: 8,
                            color:
                              i < 2
                                ? "var(--gn)"
                                : i === 2
                                  ? "var(--t3)"
                                  : "var(--mt)",
                            fontWeight: 700,
                          }}
                        >
                          {i < 2 ? "✓" : i === 2 ? "⚡" : "⏳"}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
                <div
                  style={{
                    marginTop: 12,
                    padding: 8,
                    background: "rgba(52,211,153,.04)",
                    border: "1px solid rgba(52,211,153,.07)",
                    borderRadius: 7,
                    textAlign: "center",
                    fontSize: 10,
                    color: "var(--gn)",
                    fontWeight: 600,
                  }}
                >
                  ✓ Chaque variante = hash unique
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
      <div className="divider" />

      {/* Feature 2: Scraper (reversed) */}
      <section className="feat" id="scraper">
        <div className="lp-w">
          <div className="fg rev rv">
            <div className="ft">
              <div className="flabel">📸 Scraper</div>
              <h2>
                Scrape n&apos;importe quel <span className="hl">profil.</span>
              </h2>
              <p>
                Entre un @username, récupère tous les posts, reels et vidéos TikTok. Filtre par
                date, likes, type de contenu.
              </p>
              <div className="pills">
                <span className="pill">Instagram</span>
                <span className="pill">TikTok</span>
                <span className="pill">Sans watermark</span>
                <span className="pill">Filtres</span>
              </div>
              <Link href={ctaHref} className="btn btn-p">
                Essayer gratuitement
              </Link>
            </div>
            <div className="fv">
              <div className="fm">
                <div style={{ display: "flex", gap: 6, marginBottom: 12 }}>
                  <div
                    style={{
                      flex: 1,
                      padding: 8,
                      borderRadius: 8,
                      background: "rgba(6,182,212,.05)",
                      border: "1px solid rgba(14,165,199,.12)",
                      fontSize: 10.5,
                      color: "var(--t3)",
                      fontWeight: 600,
                      textAlign: "center",
                    }}
                  >
                    📸 Instagram
                  </div>
                  <div
                    style={{
                      flex: 1,
                      padding: 8,
                      borderRadius: 8,
                      background: "var(--s2)",
                      fontSize: 10.5,
                      color: "var(--mt)",
                      textAlign: "center",
                    }}
                  >
                    🎵 TikTok
                  </div>
                </div>
                <div
                  style={{
                    background: "var(--s2)",
                    borderRadius: 8,
                    padding: "10px 12px",
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    marginBottom: 12,
                  }}
                >
                  <span style={{ fontSize: 11, color: "var(--mt)" }}>@</span>
                  <span
                    style={{
                      fontFamily: "JetBrains Mono",
                      fontSize: 11.5,
                      color: "var(--tx)",
                      fontWeight: 500,
                    }}
                  >
                    fitness_model_pro
                  </span>
                  <span
                    style={{
                      marginLeft: "auto",
                      padding: "4px 10px",
                      borderRadius: 6,
                      background: "var(--tl)",
                      color: "#fff",
                      fontSize: 9,
                      fontWeight: 700,
                    }}
                  >
                    Scraper
                  </span>
                </div>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(4, 1fr)",
                    gap: 4,
                    marginBottom: 10,
                  }}
                >
                  {[...Array(8)].map((_, i) => (
                    <div
                      key={i}
                      style={{
                        aspectRatio: 1,
                        background: i === 7 ? "rgba(14,165,199,.04)" : "var(--s3)",
                        borderRadius: 6,
                        display: "grid",
                        placeItems: "center",
                        border:
                          i === 7
                            ? "1px solid rgba(14,165,199,.1)"
                            : "1px solid var(--br)",
                        fontSize: i === 7 ? 9.5 : undefined,
                        color: i === 7 ? "var(--t3)" : undefined,
                        fontWeight: i === 7 ? 700 : undefined,
                      }}
                    >
                      {i === 7 ? (
                        "+47"
                      ) : (
                        <svg viewBox="0 0 20 20" width={16} height={16}>
                          <rect
                            x="2"
                            y="2"
                            width="16"
                            height="16"
                            rx="2"
                            fill="var(--s4)"
                          />
                          {i % 2 === 0 ? (
                            <polygon
                              points="7,6 7,14 14,10"
                              fill="var(--t3)"
                              opacity=".4"
                            />
                          ) : (
                            <circle
                              cx="7"
                              cy="8"
                              r="2"
                              fill="var(--mt)"
                              opacity=".3"
                            />
                          )}
                        </svg>
                      )}
                    </div>
                  ))}
                </div>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: 10,
                    color: "var(--dm)",
                  }}
                >
                  <span>55 fichiers</span>
                  <span style={{ color: "var(--gn)", fontWeight: 600 }}>
                    32 téléchargés
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
      <div className="divider" />

      {/* Feature 3: Modes */}
      <section className="feat" id="modes">
        <div className="lp-w">
          <div className="fg rv">
            <div className="ft">
              <div className="flabel">🛡️ Modes</div>
              <h2>
                De basique à <span className="hl">indétectable.</span>
              </h2>
              <p>
                Normal pour l&apos;usage courant. Double Process pour doubler les modifications.
                Stealth pour une uniquification maximale.
              </p>
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: 10,
                  marginBottom: 26,
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                    padding: "13px 16px",
                    background: "var(--s1)",
                    border: "1px solid var(--br)",
                    borderRadius: 10,
                  }}
                >
                  <span style={{ fontSize: 18 }}>⚡</span>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 700 }}>Normal</div>
                    <div style={{ fontSize: 11, color: "var(--dm)" }}>
                      25 techniques · Rapide
                    </div>
                  </div>
                </div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                    padding: "13px 16px",
                    background: "var(--s1)",
                    border: "1px solid rgba(167,139,250,.12)",
                    borderRadius: 10,
                  }}
                >
                  <span style={{ fontSize: 18 }}>🔥</span>
                  <div>
                    <div
                      style={{ fontSize: 13, fontWeight: 700, color: "var(--pr)" }}
                    >
                      Double Process
                    </div>
                    <div style={{ fontSize: 11, color: "var(--dm)" }}>
                      2 passes · Intensité progressive
                    </div>
                  </div>
                </div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                    padding: "13px 16px",
                    background: "var(--s1)",
                    border: "1px solid rgba(14,165,199,.15)",
                    borderRadius: 10,
                  }}
                >
                  <span style={{ fontSize: 18 }}>🛡️</span>
                  <div>
                    <div
                      style={{ fontSize: 13, fontWeight: 700, color: "var(--t3)" }}
                    >
                      Stealth
                    </div>
                    <div style={{ fontSize: 11, color: "var(--dm)" }}>
                      50+ techniques · Ordre randomisé
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="fv">
              <div className="fm">
                <div
                  style={{
                    textAlign: "center",
                    marginBottom: 14,
                    fontSize: 11,
                    fontWeight: 700,
                    color: "var(--t3)",
                  }}
                >
                  Résultat mode Stealth
                </div>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: 8,
                    marginBottom: 12,
                  }}
                >
                  <div
                    style={{
                      padding: 13,
                      background: "var(--s2)",
                      borderRadius: 8,
                      textAlign: "center",
                    }}
                  >
                    <div
                      style={{
                        fontSize: 8,
                        color: "var(--mt)",
                        textTransform: "uppercase",
                        marginBottom: 5,
                      }}
                    >
                      Hash original
                    </div>
                    <div
                      style={{
                        fontFamily: "JetBrains Mono",
                        fontSize: 10,
                        color: "var(--rd)",
                      }}
                    >
                      a3f8e2b1c4d6
                    </div>
                  </div>
                  <div
                    style={{
                      padding: 13,
                      background: "var(--s2)",
                      borderRadius: 8,
                      textAlign: "center",
                    }}
                  >
                    <div
                      style={{
                        fontSize: 8,
                        color: "var(--mt)",
                        textTransform: "uppercase",
                        marginBottom: 5,
                      }}
                    >
                      Hash variante
                    </div>
                    <div
                      style={{
                        fontFamily: "JetBrains Mono",
                        fontSize: 10,
                        color: "var(--gn)",
                      }}
                    >
                      7f2a9e3d8b1c
                    </div>
                  </div>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                  {[
                    ["Metadata", "✓ Nettoyée"],
                    ["Structure pixels", "✓ Modifiée"],
                    ["Audio fingerprint", "✓ Modifié"],
                    ["Codec signature", "✓ Modifié"],
                    ["Détection IG", "✓ 0% match"],
                  ].map(([label, val]) => (
                    <div key={label} className="fm-row">
                      <span style={{ color: "var(--dm)" }}>{label}</span>
                      <span
                        style={{
                          color: "var(--gn)",
                          fontWeight: label === "Détection IG" ? 700 : 600,
                        }}
                      >
                        {val}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Techniques Marquee */}
      <section className="tband">
        <div className="lp-w rv" style={{ textAlign: "center", marginBottom: 22 }}>
          <div className="flabel">🔬 25+ techniques</div>
          <h2
            style={{
              fontSize: "clamp(22px, 3vw, 34px)",
              fontWeight: 800,
              letterSpacing: "-1px",
            }}
          >
            Chaque détail est <span className="hl">modifié.</span>
          </h2>
        </div>
        <div style={{ overflow: "hidden" }}>
          <div className="tscroll ts1">
            {[...TECHNIQUES_1, ...TECHNIQUES_1].map((t, i) => (
              <div key={i} className="tc">
                {t}
              </div>
            ))}
          </div>
        </div>
        <div style={{ overflow: "hidden", marginTop: 10 }}>
          <div className="tscroll ts2">
            {[...TECHNIQUES_2, ...TECHNIQUES_2].map((t, i) => (
              <div key={i} className="tc">
                {t}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Social Proof */}
      <div className="divider" />
      <section className="proof">
        <div className="lp-w">
          <div className="rv" style={{ textAlign: "center", marginBottom: 48 }}>
            <div className="flabel">💬 Témoignages</div>
            <h2
              style={{
                fontSize: "clamp(22px, 3vw, 34px)",
                fontWeight: 800,
                letterSpacing: "-1px",
              }}
            >
              Ce qu&apos;en disent <span className="hl">nos utilisateurs.</span>
            </h2>
          </div>
          <div className="pcards">
            <div className="pc rv rv-d1">
              <div className="stars">★★★★★</div>
              <div className="qt">
                &quot;On est passé de 3 comptes shadow ban par semaine à zéro. Le mode Stealth
                est game changer.&quot;
              </div>
              <div className="au">Marc D.</div>
              <div className="ro">Agence OF · 12 modèles</div>
            </div>
            <div className="pc rv rv-d2">
              <div className="stars">★★★★★</div>
              <div className="qt">
                &quot;Le scraper IG + uniquification en un clic, c&apos;est un gain de temps
                énorme. 500+ fichiers/jour.&quot;
              </div>
              <div className="au">Sofia L.</div>
              <div className="ro">Content Manager</div>
            </div>
            <div className="pc rv rv-d3">
              <div className="stars">★★★★★</div>
              <div className="qt">
                &quot;Avant TikFusion à 199€. ZyChad Meta fait 10x plus pour 4x moins cher. Le
                rapport qualité/prix est fou.&quot;
              </div>
              <div className="au">Alex K.</div>
              <div className="ro">Growth Hacker</div>
            </div>
          </div>
        </div>
      </section>

      {/* Comparison */}
      <div className="divider" />
      <section style={{ padding: "100px 0" }} id="comparison">
        <div className="lp-w">
          <div className="rv" style={{ textAlign: "center", marginBottom: 48 }}>
            <div className="flabel">🔥 Comparaison</div>
            <h2
              style={{
                fontSize: "clamp(22px, 3vw, 34px)",
                fontWeight: 800,
                letterSpacing: "-1px",
              }}
            >
              ZyChad Meta vs <span className="hl">la concurrence.</span>
            </h2>
          </div>
          <div className="rv">
            <table className="ctbl">
              <thead>
                <tr>
                  <th>Feature</th>
                  <th>ZyChad Meta</th>
                  <th>TikFusion Pro</th>
                  <th>Outils manuels</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Uniquification</td>
                  <td className="y">✓ 25+ techniques</td>
                  <td>✓ Basique</td>
                  <td className="n">✗</td>
                </tr>
                <tr>
                  <td>Mode Stealth</td>
                  <td className="y">✓ 50+ techniques</td>
                  <td className="n">✗</td>
                  <td className="n">✗</td>
                </tr>
                <tr>
                  <td>Scraper IG + TikTok</td>
                  <td className="y">✓ Intégré</td>
                  <td className="n">✗</td>
                  <td className="n">✗</td>
                </tr>
                <tr>
                  <td>100% hébergé (SaaS)</td>
                  <td className="y">✓ Rien à installer</td>
                  <td className="y">✓</td>
                  <td className="n">✗</td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 700 }}>Prix</td>
                  <td style={{ color: "var(--t3)", fontWeight: 800 }}>
                    À partir de 29€/mois
                  </td>
                  <td style={{ color: "var(--rd)" }}>199€/mois</td>
                  <td style={{ color: "var(--mt)" }}>Gratuit mais galère</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="pricing" id="pricing">
        <div className="lp-w">
          <div className="ptop rv">
            <div className="flabel">💎 Tarifs</div>
            <h2
              style={{
                fontSize: "clamp(22px, 3vw, 34px)",
                fontWeight: 800,
                letterSpacing: "-1px",
                marginBottom: 6,
              }}
            >
              Choisis ton <span className="hl">plan.</span>
            </h2>
            <p
              style={{
                fontSize: 15,
                color: "var(--dm)",
                fontWeight: 300,
                marginBottom: 22,
              }}
            >
              Commence gratuitement. Upgrade quand tu es prêt.
            </p>
            <div className="trial-b">
              ✨ 3 uniquifications gratuites · Aucune carte
            </div>
          </div>
          <div className="togrow rv">
            <span className={`tl ${!yearly ? "on" : ""}`}>Mensuel</span>
            <button
              type="button"
              className={`tog ${yearly ? "on" : ""}`}
              onClick={() => setYearly(!yearly)}
              aria-label={yearly ? "Passer au mensuel" : "Passer à l'annuel"}
            />
            <span className={`tl ${yearly ? "on" : ""}`}>Annuel</span>
            <span className="sav">-20%</span>
          </div>
          <div className="pgrid">
            {PRICING_PLANS.map((plan, idx) => (
              <div
                key={plan.name}
                className={`prc rv rv-d${idx + 1} ${plan.popular ? "pop" : ""}`}
              >
                {plan.popular && (
                  <div className="pop-tag">⚡ Le plus populaire</div>
                )}
                <div className="pn">{plan.name}</div>
                <div className="pa">
                  {yearly ? plan.priceY : plan.priceM}€
                  <small>/mois</small>
                </div>
                <div className="pc">
                  {yearly ? "Facturé annuellement" : "Facturé mensuellement"}
                </div>
                <ul>
                  {plan.features.map((f) => (
                    <li key={f}>{f}</li>
                  ))}
                </ul>
                <Link
                  href={billingHref}
                  className={`pbtn ${plan.popular ? "m" : "o"}`}
                >
                  Commencer
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <div className="divider" />
      <section className="fcta">
        <div className="lp-w rv">
          <div className="fcta-card">
            <h2>
              Si tu es arrivé jusqu&apos;ici,
              <br />
              c&apos;est qu&apos;il est temps d&apos;essayer.
            </h2>
            <p>
              3 uniquifications gratuites, sans carte bancaire. Setup en 30 secondes.
            </p>
            <Link
              href={ctaHref}
              className="btn btn-p"
              style={{ fontSize: 16, padding: "15px 40px" }}
            >
              ⚡ Commencer gratuitement
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="lp-footer">
        <div className="lp-w">
          <p>
            © {new Date().getFullYear()} ZyChad Meta ·{" "}
            <Link href="/conditions">Conditions</Link> ·{" "}
            <Link href="/confidentialite">Confidentialité</Link> ·{" "}
            <Link href="/remboursement">Remboursement</Link> ·{" "}
            <Link href="/contact">Contact</Link>
          </p>
        </div>
      </footer>
    </div>
  );
}
