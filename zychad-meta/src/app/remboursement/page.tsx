import Link from "next/link";

export const metadata = {
  title: "Politique de remboursement — ZyChad Meta",
  description: "Conditions de remboursement et d'annulation pour ZyChad Meta.",
};

export default function RemboursementPage() {
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
          Politique de remboursement
        </h1>
        <p className="text-sm text-[var(--mut)] mb-12">
          Dernière mise à jour : {new Date().toLocaleDateString("fr-FR")}
        </p>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[var(--tx)] mb-4">1. Droit de rétractation</h2>
          <p>
            Conformément à la réglementation européenne sur la vente à distance, vous disposez
            d&apos;un délai de <strong>14 jours</strong> à compter de la souscription d&apos;un
            abonnement payant pour exercer votre droit de rétractation, sans avoir à justifier
            de motifs.
          </p>
          <p className="mt-4">
            Si vous avez déjà utilisé le service pendant cette période, nous nous réservons le
            droit de déduire du remboursement la valeur des services consommés (fichiers
            traités, variantes générées) au prorata.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[var(--tx)] mb-4">2. Comment demander un remboursement</h2>
          <p>
            Pour exercer votre droit de rétractation ou demander un remboursement : contactez-nous
            via la{" "}
            <Link href="/contact" className="text-[var(--t3)] hover:underline">
              page Contact
            </Link>
            {" "}
            en indiquant votre email de compte et la référence de facturation. Nous traiterons
            votre demande dans un délai de 14 jours ouvrés.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[var(--tx)] mb-4">3. Remboursements hors délai de rétractation</h2>
          <p>
            Au-delà des 14 jours, les abonnements sont en principe non remboursables. Toutefois,
            nous pouvons accorder un remboursement partiel ou total à titre exceptionnel en cas
            de : dysfonctionnement majeur du service non résolu, erreur de facturation, ou
            circonstance particulière. Chaque demande est examinée au cas par cas.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[var(--tx)] mb-4">4. Résiliation et fin d&apos;abonnement</h2>
          <p>
            Vous pouvez résilier votre abonnement à tout moment depuis votre espace de
            facturation. La résiliation prend effet à la fin de la période déjà payée. Aucun
            remboursement n&apos;est effectué pour la période en cours : vous conservez l&apos;accès
            jusqu&apos;à la date d&apos;échéance.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[var(--tx)] mb-4">5. Modalités du remboursement</h2>
          <p>
            Le remboursement est effectué sur le même moyen de paiement que celui utilisé pour
            l&apos;achat, dans un délai de 14 jours suivant l&apos;acceptation de la demande. Les
            remboursements sont traités par notre prestataire de paiement Paddle.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[var(--tx)] mb-4">6. Essai gratuit</h2>
          <p>
            L&apos;essai gratuit (3 uniquifications) ne donne lieu à aucun engagement ni
            facturation. Aucune carte bancaire n&apos;est requise pour l&apos;essai. Si vous
            souscrivez à un plan payant après l&apos;essai, les conditions de remboursement
            ci-dessus s&apos;appliquent.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[var(--tx)] mb-4">7. Contact</h2>
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
          <Link href="/conditions" className="text-[var(--dm)] hover:underline">
            Conditions
          </Link>
          {" · "}
          <Link href="/confidentialite" className="text-[var(--dm)] hover:underline">
            Confidentialité
          </Link>
        </div>
      </footer>
    </div>
  );
}
