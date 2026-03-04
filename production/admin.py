from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from django.db.models import Sum
from .models import *


# ===== FORMSET PERSONNALISÉ =====
class FormuleInlineFormSet(BaseInlineFormSet):

    def clean(self):
        super().clean()

        total = 0

        for form in self.forms:
            if not form.cleaned_data:
                continue

            if form.cleaned_data.get("DELETE"):
                continue

            total += form.cleaned_data.get("pourcentage", 0)

        # Tolérance arrondi
        if round(total, 2) != 100:
            raise ValidationError(
                f"La formule doit faire exactement 100%. Total actuel : {total}%"
            )


# ===== INLINE =====
class FormuleInline(admin.TabularInline):
    model = Formule
    extra = 1
    formset = FormuleInlineFormSet


# ===== Matière première =====
class MatierePremiereAdmin(admin.ModelAdmin):
    list_display = ("nom", "stock_actuel", "stock_minimum", "unite")
    search_fields = ("nom",)


# ===== Produit =====
class ProduitAdmin(admin.ModelAdmin):
    list_display = ("nom", "gamme", "stock_actuel", "total_pourcentage")
    list_filter = ("gamme",)
    inlines = [FormuleInline]
    readonly_fields = ("total_pourcentage",)


# ===== Action production =====
@admin.action(description="Lancer la production")
def lancer_production(modeladmin, request, queryset):
    succes = 0

    for ordre in queryset:
        try:
            ordre.lancer_production()
            succes += 1
        except ValidationError as e:
            modeladmin.message_user(
                request,
                f"Erreur pour {ordre.produit} : {e}",
                level=messages.ERROR
            )

    if succes:
        modeladmin.message_user(
            request,
            f"{succes} production(s) lancée(s) avec succès.",
            level=messages.SUCCESS
        )


# ===== Ordre fabrication =====
class OrdreFabricationAdmin(admin.ModelAdmin):
    list_display = ("produit", "quantite_a_produire", "statut", "date_creation")
    list_filter = ("statut", "date_creation")
    actions = [lancer_production]


# ===== Mouvement stock =====
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ("type_mouvement", "produit", "matiere", "quantite", "date")
    list_filter = ("type_mouvement", "date")

class ClientAdmin(admin.ModelAdmin):
    list_display = ("nom", "telephone")
    search_fields = ("nom",)


class LivraisonAdmin(admin.ModelAdmin):
    list_display = ("produit", "client", "quantite", "statut", "date_livraison")
    list_filter = ("statut", "date_livraison")
    search_fields = ("client__nom",)

class LotProductionAdmin(admin.ModelAdmin):
    list_display = ("numero_lot", "ordre", "quantite_produite", "date_production")


class RetourProduitAdmin(admin.ModelAdmin):
    list_display = ("livraison", "quantite", "date_retour")


admin.site.register(LotProduction, LotProductionAdmin)
admin.site.register(RetourProduit, RetourProduitAdmin)


admin.site.register(Client, ClientAdmin)
admin.site.register(Livraison, LivraisonAdmin)


admin.site.register(MatierePremiere, MatierePremiereAdmin)
admin.site.register(Produit, ProduitAdmin)
admin.site.register(OrdreFabrication, OrdreFabricationAdmin)
admin.site.register(MouvementStock, MouvementStockAdmin)