from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


# =========================
# Matières premières
# =========================
class MatierePremiere(models.Model):

    TYPES = [
        ("base", "Matière première"),
        ("premix", "Premix / Additif"),
    ]

    nom = models.CharField(max_length=150)
    type_matiere = models.CharField(max_length=20, choices=TYPES, default="base")
    stock_actuel = models.FloatField(default=0)
    stock_minimum = models.FloatField(default=0)
    unite = models.CharField(default="tonnes", max_length=20)

    def __str__(self):
        return self.nom


# =========================
# Produits fabriqués
# =========================
class Produit(models.Model):

    GAMMES = [
        ("pondeuse", "Gamme Pondeuse"),
        ("chair", "Gamme Chair"),
        ("concentre", "Gamme Concentré"),
        ("ruminant", "Gamme Ruminant"),
    ]

    SOUS_GAMMES = [

        # ===== PONDEUSE =====
        ("poulette_demarrage", "Poulette démarrage 0-8 semaines"),
        ("poulette_finition", "Poulette finition 8-18 semaines"),
        ("pre_ponte", "Poulette pré-ponte 18-21 semaines"),
        ("pondeuse_22_50", "Pondeuse 22-50 semaines"),
        ("pondeuse_50_90", "Pondeuse 50-90 semaines"),

        # ===== CHAIR =====
        ("prestarter", "Prestarter 0-7 jours"),
        ("chair_demarrage", "Chair démarrage 7-21 jours"),
        ("chair_finition", "Chair finition 21-35 jours"),

        # ===== CONCENTRE =====
        ("concentre_20_pondeuse", "Concentré 20% pondeuse"),
        ("concentre_30_chair", "Concentré 30% chair"),
        ("concentre_2_5_pondeuse", "Concentré 2,5% pondeuse"),

        # ===== RUMINANT =====
        ("vache_laitiere_18", "Vache laitière 18%"),
        ("super_embouche", "Super embouche"),
        ("super_ruminant_entretien", "Super ruminant entretien"),
    ]

    nom = models.CharField(max_length=150)
    gamme = models.CharField(max_length=50, choices=GAMMES)
    sous_gamme = models.CharField(max_length=100, choices=SOUS_GAMMES)
    stock_actuel = models.FloatField(default=0)

    def __str__(self):
        return f"{self.nom} ({self.get_sous_gamme_display()})"

    def total_pourcentage(self):
        from django.db.models import Sum
        total = Formule.objects.filter(produit=self).aggregate(
            total=Sum("pourcentage")
        )["total"] or 0
        return f"{round(total,2)}%"

#-----------
# =========================
# Lot de production
# =========================




# =========================
# Formules fabrication
# =========================
class Formule(models.Model):

    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    matiere_premiere = models.ForeignKey(MatierePremiere, on_delete=models.CASCADE)
    pourcentage = models.FloatField(help_text="Ex: 60 = 60%")

    def clean(self):

        if not self.produit_id:
            return

        from django.db.models import Sum

        total = Formule.objects.filter(produit=self.produit)\
            .exclude(id=self.id)\
            .aggregate(total=Sum("pourcentage"))["total"] or 0

        total += self.pourcentage

        if total > 100:
            raise ValidationError(
                f"Total dépasse 100%. Total actuel : {total}%"
            )


# =========================
# Ordre de fabrication
# =========================
class OrdreFabrication(models.Model):
    # Création du lot
    
    STATUTS = [
        ("attente", "En attente"),
        ("termine", "Terminé"),
    ]

    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite_a_produire = models.FloatField(help_text="Quantité en tonnes")
    statut = models.CharField(max_length=20, choices=STATUTS, default="attente")
    date_creation = models.DateTimeField(auto_now_add=True)
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.produit} - {self.quantite_a_produire} tonnes"

    def lancer_production(self):

        from django.db.models import Sum

        total = Formule.objects.filter(produit=self.produit).aggregate(
            total=Sum("pourcentage")
        )["total"] or 0

        if round(total,2) != 100:
            raise ValidationError(
                f"Formule invalide. Total actuel : {total}%"
            )

        formules = Formule.objects.filter(produit=self.produit)

        manque = []

        for formule in formules:
            matiere = formule.matiere_premiere
            quantite_necessaire = (formule.pourcentage / 100) * self.quantite_a_produire

            if matiere.stock_actuel < quantite_necessaire:
                manque.append(
                    f"{matiere.nom} : "
                    f"{round(quantite_necessaire - matiere.stock_actuel,2)} tonnes manquantes"
                )

        if manque:
            raise ValidationError(f"Stock insuffisant : {', '.join(manque)}")

        # Déduction
        for formule in formules:
            matiere = formule.matiere_premiere
            quantite_necessaire = (formule.pourcentage / 100) * self.quantite_a_produire

            matiere.stock_actuel -= quantite_necessaire
            matiere.save()

            MouvementStock.objects.create(
                type_mouvement="sortie",
                matiere=matiere,
                quantite=quantite_necessaire
            )

        # Ajout produit fini
        self.produit.stock_actuel += self.quantite_a_produire
        self.produit.save()

        MouvementStock.objects.create(
            type_mouvement="entree",
            produit=self.produit,
            quantite=self.quantite_a_produire
        )
        from django.utils import timezone
        import uuid

        numero = f"LOT-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:5].upper()}"
        numero = f"LOT-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:5].upper()}"
        
        LotProduction.objects.create(
            ordre=self,
            numero_lot=numero,
            quantite_produite=self.quantite_a_produire
        )
    

        self.statut = "termine"
        self.save()
        

# =========================
# Lot de Production
# =========================
class LotProduction(models.Model):

    ordre = models.ForeignKey(
        OrdreFabrication,
        on_delete=models.CASCADE,
        related_name="lots"
    )

    numero_lot = models.CharField(max_length=50, unique=True)
    quantite_produite = models.FloatField()
    date_production = models.DateTimeField(auto_now_add=True)

    # Suivi performance
    temps_production_heures = models.FloatField(null=True, blank=True)
    rendement = models.FloatField(null=True, blank=True)  # %

    def __str__(self):
        return f"Lot {self.numero_lot} - {self.quantite_produite} T"

# =========================
# Mouvement stock
# =========================
class MouvementStock(models.Model):

    TYPES = [
        ("entree", "Entrée"),
        ("sortie", "Sortie"),
    ]

    type_mouvement = models.CharField(max_length=10, choices=TYPES)
    produit = models.ForeignKey(Produit, null=True, blank=True, on_delete=models.CASCADE)
    matiere = models.ForeignKey(MatierePremiere, null=True, blank=True, on_delete=models.CASCADE)
    quantite = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type_mouvement} - {self.quantite} tonnes"
    



    # =========================
# Clients
# =========================
class Client(models.Model):
    nom = models.CharField(max_length=150)
    telephone = models.CharField(max_length=30, blank=True)
    adresse = models.CharField(max_length=200, blank=True)
    def __str__(self):
        return self.nom
    


# =========================
# Livraison Produits
# =========================
# =========================
# Livraison Produits
# =========================
class Livraison(models.Model):

    STATUTS = [
        ("prepare", "Préparée"),
        ("livre", "Livrée"),
        ("retour", "Retour"),
    ]

    lot = models.ForeignKey(
        LotProduction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    quantite = models.FloatField()
    destination = models.CharField(max_length=200)
    date_livraison = models.DateField()
    statut = models.CharField(max_length=20, choices=STATUTS, default="prepare")
    date_creation = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.produit.stock_actuel < self.quantite:
            manque = round(self.quantite - self.produit.stock_actuel, 2)
            raise ValidationError(
                f"Stock insuffisant. Il manque {manque} tonnes."
            )

    def save(self, *args, **kwargs):

        if not self.pk:
            self.produit.stock_actuel -= self.quantite
            self.produit.save()

            MouvementStock.objects.create(
                type_mouvement="sortie",
                produit=self.produit,
                quantite=self.quantite
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.produit} → {self.client} ({self.quantite} T)"
    




# =========================
# Retour Produit
# =========================
class RetourProduit(models.Model):

    livraison = models.ForeignKey(Livraison, on_delete=models.CASCADE)
    quantite = models.FloatField()
    motif = models.TextField()
    date_retour = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):

        # Retour augmente le stock
        self.livraison.produit.stock_actuel += self.quantite
        self.livraison.produit.save()

        MouvementStock.objects.create(
            type_mouvement="entree",
            produit=self.livraison.produit,
            quantite=self.quantite
        )

        super().save(*args, **kwargs)    