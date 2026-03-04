from django import forms
from .models import Produit, MatierePremiere, OrdreFabrication, Livraison


class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = '__all__'


class MatiereForm(forms.ModelForm):
    class Meta:
        model = MatierePremiere
        fields = '__all__'


class OrdreForm(forms.ModelForm):
    class Meta:
        model = OrdreFabrication
        fields = '__all__'


class LivraisonForm(forms.ModelForm):
    class Meta:
        model = Livraison
        fields = '__all__'