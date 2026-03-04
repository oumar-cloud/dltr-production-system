from django.urls import path
from . import views

urlpatterns = [

    # PRODUITS
    path('produits/', views.produits_list, name='produits'),
    path('produits/add/', views.produit_create, name='produit_add'),
    path('produits/edit/<int:pk>/', views.produit_edit, name='produit_edit'),
    path('produits/delete/<int:pk>/', views.produit_delete, name='produit_delete'),

    # MATIERES
    path('matieres/', views.matieres_list, name='matieres'),
    path('matieres/add/', views.matiere_create, name='matiere_add'),
    path('matieres/edit/<int:pk>/', views.matiere_edit, name='matiere_edit'),
    path('matieres/delete/<int:pk>/', views.matiere_delete, name='matiere_delete'),

    # ORDRES
    path('ordres/', views.ordres_list, name='ordres'),
    path('ordres/add/', views.ordre_create, name='ordre_add'),
    path('ordres/execute/<int:pk>/', views.ordre_execute, name='ordre_execute'),

    # LIVRAISONS
    path('livraisons/', views.livraisons_list, name='livraisons'),
    path('livraisons/add/', views.livraison_create, name='livraison_add'),
]