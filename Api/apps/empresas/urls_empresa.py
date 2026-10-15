from django.urls import path
from .views import RegistroEmpresaView, ObtenerEmpresaView, BuscarCiiuPublicoView

urlpatterns = [
    path("registro", RegistroEmpresaView.as_view(), name="empresa-registro"),
    path("ciiu/buscar", BuscarCiiuPublicoView.as_view(), name="empresa-ciiu-buscar"),
    path("<uuid:id>", ObtenerEmpresaView.as_view(), name="empresa-detalle"),
]
