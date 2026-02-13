const FEATURES = [
  {
    title: "Vidéo",
    desc: "Vitesse ±3-4%, luminosité/contraste/saturation, crop+zoom, FPS, audio (tempo, pitch, EQ), metadata spoof, et plus.",
  },
  {
    title: "Image",
    desc: "Micro-rotation, crop+zoom, gradient overlay, gamma local, bruit, chromatic aberration, EXIF spoof, format aléatoire.",
  },
  {
    title: "Modes",
    desc: "Normal, Double Process (2 passes), Stealth (metadata strip + ordre aléatoire).",
  },
  {
    title: "Scale",
    desc: "Upload direct S3, queue BullMQ, workers Python en Docker. Prêt pour 1000+ utilisateurs simultanés.",
  },
  {
    title: "Sécurité",
    desc: "Code de processing jamais exposé au client. Rate limiting, CSRF, validation stricte des fichiers.",
  },
  {
    title: "Paddle",
    desc: "Paiement et TVA gérés par Paddle. Abonnements mensuels ou annuels avec -20%.",
  },
];

export function Features() {
  return (
    <section className="container mx-auto px-4 py-20 border-t border-[var(--zychad-border)]">
      <h2 className="text-3xl font-bold text-center mb-12 text-[var(--zychad-text)]">
        Ce que tu obtiens
      </h2>
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {FEATURES.map((f) => (
          <div
            key={f.title}
            className="p-6 rounded-lg border border-[var(--zychad-border)] bg-[var(--zychad-surface)]"
          >
            <h3 className="text-lg font-semibold text-[var(--zychad-teal-bright)] mb-2">{f.title}</h3>
            <p className="text-sm text-[var(--zychad-dim)]">{f.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
