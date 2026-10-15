from django.urls import path
from .views import (
    InformeListView,
    InformeGenerarView,
    InformeDetalleView,
    InformeGuardarBorradorView,
    InformeFinalizarView,
    InformeDescartarBorradorView,
    InformeFirmarView,
    InformeDescargarPDFView,
)

urlpatterns = [
    path("informes/", InformeListView.as_view(), name="informe-list"),
    path("informes/generar", InformeGenerarView.as_view(), name="informe-generar"),
    path("informes/<uuid:informe_id>", InformeDetalleView.as_view(), name="informe-detalle"),
    path("informes/<uuid:informe_id>/guardar-borrador", InformeGuardarBorradorView.as_view(), name="informe-guardar-borrador"),
    path("informes/<uuid:informe_id>/finalizar", InformeFinalizarView.as_view(), name="informe-finalizar"),
    path("informes/<uuid:informe_id>/descartar-borrador", InformeDescartarBorradorView.as_view(), name="informe-descartar-borrador"),
    path("informes/<uuid:informe_id>/firmar", InformeFirmarView.as_view(), name="informe-firmar"),
    path("informes/<uuid:informe_id>/descargar-pdf", InformeDescargarPDFView.as_view(), name="informe-descargar-pdf"),
]
