import Link from "next/link";

export const metadata = {
  title: "Conditions d'utilisation — ZyChad Meta",
  description: "Conditions générales d'utilisation du service ZyChad Meta.",
};

export default function ConditionsPage() {
  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--tx)]">
      <header className="border-b border-[var(--br)] py-6">
        <div className="max-w-3xl mx-auto px-6">
          <Link href="/" className="text-[var(--t3)] hover:underline font-semibold">
            ← Retour
          </Link>
        </div>
      </header>
      <main className="max-w-3xl mx-auto px-6 py-12 prose prose-invert prose-headings:text-[var(--tx)] prose-p:text-[var(--dm)] prose-li:text-[var(--dm)]">
        <h1 className="text-3xl font-bold text-[var(--tx)] mb-2">
          Conditions d&apos;utilisation
        </h1>
        <p className="text-sm text-[var(--mut)] mb-12">
          Dernière mise à jour : {new Date().toLocaleDateString("fr-FR")}
        </p>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[var(--tx)] mb-4">1. Objet</h2>
          <p>
            Les présentes conditions générales d&apos;utilisation (CGU) régissent l&apos;accès et
            l&apos;utilisation du service ZyChad Meta, plateforme SaaS d&apos;uniquification de
            vidéos et d&apos;images pour les réseaux sociaux (Instagram, TikTok, etc.). En
            utilisant notre service, vous acceptez ces conditions.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[var(--tx)] mb-4">2. Description du service</h2>
          <p>
            ZyChad Meta propose des outils d&apos;uniquification de contenus multimédias (vidéos,
            images) afin de contourner la détection de contenu dupliqué sur les plateformes
            sociales. Le service inclut notamment : upload de fichiers, génération de variantes,
            scraper Instagram/TikTok, et différents modes de traitement (Normal, Double Process,
            Stealth).
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[var(--tx)] mb-4">3. Compte utilisateur</h2>
          <p>
            L&apos;inscription est requise pour accéder aux fonctionnalités payantes. Vous vous
            engagez à fournir des informations exactes et à maintenir la confidentialité de votre
            mot de passe. Vous êtes responsable des activités effectuées sous votre compte.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[var(--tx)] mb-4">4. Tarification et facturation</h2>
          <p>
            Les tarifs sont indiqués sur la page de tarification. Les abonnements sont facturés
            mensuellement ou annuellement selon le plan choisi. Les prix peuvent être modifiés
            avec un préavis raisonnable. En cas de changement, vous pourrez résilier avant la
            prochaine facturation.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[var(--tx)] mb-4">5. Utilisation acceptable</h2>
          <p>Vous vous engagez à :</p>
          <ul className="list-disc pl-6 mt-2 space-y-1">
            <li>Ne pas utiliser le service à des fins illégales ou contraires aux CGU des plateformes tierces</li>
            <li>Ne pas contourner les limitations techniques du service</li>
            <li>Ne pas partager votre compte ou vos identifiants API de manière abusive</li>
            <li>Respecter les quotas et limites de votre plan</li>
          </ul>
          <p className="mt-4">
            Nous nous réservons le droit de suspendre ou résilier tout compte en cas de violation.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[var(--tx)] mb-4">6. Propriété intellectuelle</h2>
          <p>
            ZyChad Meta conserve tous les droits sur la plateforme, le code, les marques et le
            contenu du service. Vous conservez la propriété de vos fichiers uploadés. En
            utilisant le service, vous nous accordez une licence limitée pour traiter vos fichiers
            afin de fournir le service.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[var(--tx)] mb-4">7. Limitation de responsabilité</h2>
          <p>
            Le service est fourni &quot;en l&apos;état&quot;. Nous ne garantissons pas un taux
            d&apos;unicité ou une absence de détection à 100 %. Nous déclinons toute responsabilité
            pour les conséquences liées à l&apos;utilisation de vos contenus sur les plateformes
            tierces (shadowban, suspension de compte, etc.).
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[var(--tx)] mb-4">8. Résiliation</h2>
          <p>
            Vous pouvez résilier votre abonnement à tout moment depuis votre espace de facturation.
            La résiliation prend effet à la fin de la période en cours. Aucun remboursement
            partiel ne sera effectué pour la période déjà facturée. Consultez notre{" "}
            <Link href="/remboursement" className="text-[var(--t3)] hover:underline">
              politique de remboursement
            </Link>{" "}
            pour plus de détails.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[var(--tx)] mb-4">9. Modifications</h2>
          <p>
            Nous pouvons modifier ces CGU. Les utilisateurs seront informés par email ou via une
            notification dans l&apos;application. La poursuite de l&apos;utilisation après
            modification vaut acceptation des nouvelles conditions.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[var(--tx)] mb-4">10. Contact</h2>
          <p>
            Pour toute question :{" "}
            <Link href="/contact" className="text-[var(--t3)] hover:underline">
              page Contact
            </Link>
            .
          </p>
        </section>
      </main>
      <footer className="border-t border-[var(--br)] py-6 mt-12">
        <div className="max-w-3xl mx-auto px-6 text-center text-sm text-[var(--mut)]">
          <Link href="/" className="text-[var(--t3)] hover:underline">
            ZyChad Meta
          </Link>
          {" · "}
          <Link href="/confidentialite" className="text-[var(--dm)] hover:underline">
            Confidentialité
          </Link>
          {" · "}
          <Link href="/remboursement" className="text-[var(--dm)] hover:underline">
            Remboursement
          </Link>
        </div>
      </footer>
    </div>
  );
}
