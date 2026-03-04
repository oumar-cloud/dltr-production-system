from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Produit, MatierePremiere, OrdreFabrication, Livraison
from .forms import ProduitForm, MatiereForm, OrdreForm, LivraisonForm


# ================= PRODUITS =================

@login_required
def produits_list(request):
    produits = Produit.objects.all()
    return render(request, "production/produits_list.html", {"produits": produits})


@login_required
def produit_create(request):
    form = ProduitForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Produit ajouté")
        return redirect("produits")
    return render(request, "production/produit_form.html", {"form": form})


@login_required
def produit_edit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    form = ProduitForm(request.POST or None, instance=produit)
    if form.is_valid():
        form.save()
        messages.success(request, "Produit modifié")
        return redirect("produits")
    return render(request, "production/produit_form.html", {"form": form})


@login_required
def produit_delete(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    produit.delete()
    messages.success(request, "Produit supprimé")
    return redirect("produits")


# ================= MATIERES =================

@login_required
def matieres_list(request):
    matieres = MatierePremiere.objects.all()
    return render(request, "production/matieres_list.html", {"matieres": matieres})


@login_required
def matiere_create(request):
    form = MatiereForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("matieres")
    return render(request, "production/matiere_form.html", {"form": form})


@login_required
def matiere_edit(request, pk):
    matiere = get_object_or_404(MatierePremiere, pk=pk)
    form = MatiereForm(request.POST or None, instance=matiere)
    if form.is_valid():
        form.save()
        return redirect("matieres")
    return render(request, "production/matiere_form.html", {"form": form})


@login_required
def matiere_delete(request, pk):
    matiere = get_object_or_404(MatierePremiere, pk=pk)
    matiere.delete()
    return redirect("matieres")


# ================= ORDRES =================

@login_required
def ordres_list(request):
    ordres = OrdreFabrication.objects.all()
    return render(request, "production/ordres_list.html", {"ordres": ordres})


@login_required
def ordre_create(request):
    form = OrdreForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("ordres")
    return render(request, "production/ordre_form.html", {"form": form})


@login_required
def ordre_execute(request, pk):
    ordre = get_object_or_404(OrdreFabrication, pk=pk)

    if ordre.statut != "termine":
        try:
            ordre.lancer_production()   # ✅ TON vrai nom de méthode
            messages.success(request, "Production exécutée avec succès.")
        except Exception as e:
            messages.error(request, f"Erreur : {e}")

    return redirect("ordres")


# ================= LIVRAISONS =================

@login_required
def livraisons_list(request):
    livraisons = Livraison.objects.all()
    return render(request, "production/livraisons_list.html", {"livraisons": livraisons})


@login_required
def livraison_create(request):
    form = LivraisonForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Livraison créée")
        return redirect("livraisons")
    return render(request, "production/livraison_form.html", {"form": form})