from django.shortcuts import render
from django.db import models
from django.db.models import Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required

from production.models import (
    MatierePremiere,
    Produit,
    MouvementStock,
    LotProduction,
    Livraison,
    RetourProduit,
    OrdreFabrication
)


@login_required(login_url='/login/')
def index(request):

    now = timezone.now()
    current_year = now.year
    current_month = now.month
    today = now


    # ================= KPI STOCK =================

    total_matieres = MatierePremiere.objects.aggregate(
        total=Sum("stock_actuel")
    )["total"] or 0

    total_produits = Produit.objects.aggregate(
        total=Sum("stock_actuel")
    )["total"] or 0

    total_mouvements = MouvementStock.objects.count()


    # ================= PRODUCTION =================

    production_mois = LotProduction.objects.filter(
        date_production__month=current_month,
        date_production__year=current_year
    ).aggregate(total=Sum("quantite_produite"))["total"] or 0

    rendement_moyen = LotProduction.objects.exclude(
        rendement__isnull=True
    ).aggregate(avg=Avg("rendement"))["avg"]

    rendement_moyen = round(rendement_moyen, 2) if rendement_moyen else 0


    # ================= LIVRAISONS =================

    total_livraisons = Livraison.objects.count()
    livrees = Livraison.objects.filter(statut="livre").count()
    total_retours = RetourProduit.objects.count()

    taux_livraison = round((livrees / total_livraisons) * 100, 2) if total_livraisons else 0
    taux_retour = round((total_retours / total_livraisons) * 100, 2) if total_livraisons else 0


    # ================= MATIERES =================

    matieres = MatierePremiere.objects.all()

    matieres_alertes = matieres.filter(
        stock_actuel__lte=models.F("stock_minimum")
    )


    # ================= PREVISION RUPTURE =================

    matieres_risque = []

    for matiere in matieres:

        consommation_30j = MouvementStock.objects.filter(
            type_mouvement="sortie",
            matiere=matiere,
            date__gte=today - timedelta(days=30)
        ).aggregate(total=Sum("quantite"))["total"] or 0

        if consommation_30j > 0:

            conso_jour = consommation_30j / 30
            jours_restants = matiere.stock_actuel / conso_jour if conso_jour else 999

            if jours_restants < 30:

                matieres_risque.append({
                    "nom": matiere.nom,
                    "jours_restants": round(jours_restants, 1)
                })


    # ================= ROTATION STOCK =================

    consommation_totale = MouvementStock.objects.filter(
        type_mouvement="sortie"
    ).aggregate(total=Sum("quantite"))["total"] or 0

    rotation_stock = round(consommation_totale / total_matieres, 2) if total_matieres else 0


    # ================= DONNEES GRAPHIQUES =================

    mois_labels = []
    production_data = []
    rendement_data = []
    livraison_data = []

    for month in range(1, 13):

        total_prod = LotProduction.objects.filter(
            date_production__month=month,
            date_production__year=current_year
        ).aggregate(total=Sum("quantite_produite"))["total"] or 0

        avg_rend = LotProduction.objects.filter(
            date_production__month=month,
            date_production__year=current_year
        ).exclude(rendement__isnull=True)\
         .aggregate(avg=Avg("rendement"))["avg"] or 0

        total_livr = Livraison.objects.filter(
            date_livraison__month=month,
            date_livraison__year=current_year
        ).count()

        mois_labels.append(datetime(current_year, month, 1).strftime("%b"))
        production_data.append(float(total_prod))
        rendement_data.append(round(float(avg_rend), 2))
        livraison_data.append(total_livr)


    # ================= TENDANCE ANNUELLE =================

    annees = [current_year - 2, current_year - 1, current_year]
    tendances = []

    for annee in annees:

        total = LotProduction.objects.filter(
            date_production__year=annee
        ).aggregate(total=Sum("quantite_produite"))["total"] or 0

        tendances.append(float(total))


    # ================= SCORE GLOBAL =================

    score_usine = round(
        (rendement_moyen * 0.4) +
        (taux_livraison * 0.3) +
        ((100 - taux_retour) * 0.3),
        1
    )


    # ================= DERNIERS ORDRES =================

    ordres = OrdreFabrication.objects.order_by("-id")[:5]


    # ================= CONTEXT =================

    context = {

        "total_matieres": round(total_matieres, 2),
        "total_produits": round(total_produits, 2),
        "total_mouvements": total_mouvements,
        "rotation_stock": rotation_stock,

        "production_mois": round(production_mois, 2),
        "rendement_moyen": rendement_moyen,

        "taux_livraison": taux_livraison,
        "taux_retour": taux_retour,

        "score_usine": score_usine,

        "mois_labels": mois_labels,
        "production_data": production_data,
        "rendement_data": rendement_data,
        "livraison_data": livraison_data,

        "matieres_alertes": matieres_alertes,
        "matieres_risque": matieres_risque,

        "annees": annees,
        "tendances": tendances,

        "ordres": ordres,
    }

    return render(request, "index.html", context)



def samplepage(request):
    return render(request, "sample-page.html")


def custom_404(request, exception):
    return render(request, "404.html", status=404)