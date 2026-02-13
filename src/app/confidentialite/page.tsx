import Link from "next/link";

export const metadata = {
  title: "Politique de confidentialité — ZyChad Meta",
  description: "Comment ZyChad Meta collecte et protège vos données personnelles.",
};

export default function ConfidentialitePage() {
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
          Politique de confidentialité
        </h1>
        <p className="text-sm text-[var(--mut)] mb-12">
          Dernière mise à jour : {new Date().toLocaleDateString("fr-FR")}
        </p>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[var(--tx)] mb-4">1. Responsable du traitement</h2>
          <p>
            ZyChad Meta est le responsable du traitement des données personnelles collectées via
            le service zychadmeta.com et l&apos;application associée.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[var(--tx)] mb-4">2. Données collectées</h2>
          <p>Nous collectons les données suivantes :</p>
          <ul className="list-disc pl-6 mt-2 space-y-1">
            <li><strong>Compte :</strong> email, nom (optionnel), mot de passe (hashé)</li>
            <li><strong>Paiement :</strong> informations de facturation via notre prestataire Paddle (email, adresse de facturation)</li>
            <li><strong>Usage :</strong> fichiers uploadés pour traitement, métadonnées des jobs (statut, nombre de variantes, mode)</li>
            <li><strong>Technique :</strong> adresse IP, logs d&apos;accès, identifiant de session</li>
          </ul>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[var(--tx)] mb-4">3. Finalités du traitement</h2>
          <p>
            Les données sont utilisées pour : fournir le service d&apos;uniquification, gérer
            votre compte et votre abonnement, traiter les paiements, assurer la sécurité et le
            bon fonctionnement de la plateforme, et respecter nos obligations légales.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[var(--tx)] mb-4">4. Base légale</h2>
          <p>
            Le traitement repose sur : l&apos;exécution du contrat (fourniture du service), votre
            consentement (newsletter, cookies non essentiels), et notre intérêt légitime
            (sécurité, amélioration du service).
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[var(--tx)] mb-4">5. Conservation</h2>
          <p>
            Les fichiers uploadés sont traités et supprimés après génération des variantes (ou
            selon la durée de rétention définie pour votre plan). Les données de compte sont
            conservées tant que votre compte est actif, puis archivées conformément aux
            obligations légales (facturation : 10 ans en France).
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[var(--tx)] mb-4">6. Partage des données</h2>
          <p>
            Nous ne vendons pas vos données. Elles peuvent être partagées avec : notre
            prestataire de paiement (Paddle), notre hébergeur, et les services d&apos;infrastructure
            (stockage, CDN) nécessaires au fonctionnement du service. Ces prestataires sont
            soumis à des obligations contractuelles de confidentialité.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[var(--tx)] mb-4">7. Vos droits (RGPD)</h2>
          <p>Vous disposez des droits suivants :</p>
          <ul className="list-disc pl-6 mt-2 space-y-1">
            <li><strong>Accès :</strong> obtenir une copie de vos données</li>
            <li><strong>Rectification :</strong> corriger des données inexactes</li>
            <li><strong>Effacement :</strong> demander la suppression de vos données</li>
            <li><strong>Portabilité :</strong> recevoir vos données dans un format structuré</li>
            <li><strong>Opposition / limitation :</strong> dans les cas prévus par la loi</li>
          </ul>
          <p className="mt-4">
            Pour exercer ces droits, contactez-nous via la{" "}
            <Link href="/contact" className="text-[var(--t3)] hover:underline">
              page Contact
            </Link>
            . Vous pouvez également introduire une réclamation auprès de la CNIL (France).
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[var(--tx)] mb-4">8. Cookies</h2>
          <p>
            Nous utilisons des cookies essentiels (session, authentification) et, le cas échéant,
            des cookies d&apos;analyse pour améliorer le service. Vous pouvez configurer votre
            navigateur pour refuser les cookies non essentiels.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[var(--tx)] mb-4">9. Sécurité</h2>
          <p>
            Nous mettons en œuvre des mesures techniques et organisationnelles (chiffrement
            HTTPS, stockage sécurisé, accès restreint) pour protéger vos données contre tout
            accès, modification ou divulgation non autorisés.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[var(--tx)] mb-4">10. Contact</h2>
          <p>
            Pour toute question relative à la confidentialité :{" "}
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
          <Link href="/conditions" className="text-[var(--dm)] hover:underline">
            Conditions
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
