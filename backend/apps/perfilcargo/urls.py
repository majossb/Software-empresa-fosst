from django.urls import path
from .views import (
    PerfilCargoListView, PerfilCargoDetailView, PerfilCargoVersionesView,
    SuggestedEPPsView, GenerateIAFieldView, GeneratePDFView, PDFStatusView,
    CatalogoPeligrosView, CatalogoEPPsView, SugerirPeligrosEPPsCargoView
)

urlpatterns = [
    path('perfil-cargo', PerfilCargoListView.as_view(), name='perfil-cargo-list'),
    path('perfil-cargo/generar-ia', GenerateIAFieldView.as_view(), name='perfil-cargo-generar-ia'),
    path('perfil-cargo/sugerir-peligros-epps', SugerirPeligrosEPPsCargoView.as_view(), name='perfil-cargo-sugerir-peligros-epps'),
    path('perfil-cargo/<uuid:pk>', PerfilCargoDetailView.as_view(), name='perfil-cargo-detail'),
    path('perfil-cargo/<uuid:pk>/versiones', PerfilCargoVersionesView.as_view(), name='perfil-cargo-versiones'),
    path('perfil-cargo/<uuid:pk>/pdf', GeneratePDFView.as_view(), name='perfil-cargo-pdf'),
    path('perfil-cargo/<uuid:pk>/pdf/estado', PDFStatusView.as_view(), name='perfil-cargo-pdf-estado'),
    
    path('peligros/<uuid:pk>/epps', SuggestedEPPsView.as_view(), name='peligros-epps-sugeridos'),
    
    path('catalogos/peligros', CatalogoPeligrosView.as_view(), name='catalogo-peligros'),
    path('catalogos/epps', CatalogoEPPsView.as_view(), name='catalogo-epps'),
]
