from django.urls import path
from .views import (
    ContextoEmpresaView,
    UploadLogoEmpresaView,
    ResumenCompletitudView,
    SugerirCiiuIAView,
    DescribirCiiuIAView,
    UpdateIdentidadView,
    SugerirIdentidadIAView,
    TransicionCapituloView,
    HistorialTransicionesCapituloView,
)

urlpatterns = [
    path("contexto", ContextoEmpresaView.as_view(), name="modulo0-contexto"),
    path("contexto/logo", UploadLogoEmpresaView.as_view(), name="modulo0-logo"),
    path("completitud", ResumenCompletitudView.as_view(), name="modulo0-completitud"),
    path("contexto/ciiu/sugerir", SugerirCiiuIAView.as_view(), name="modulo0-ciiu-sugerir"),
    path("contexto/ciiu/describir", DescribirCiiuIAView.as_view(), name="modulo0-ciiu-describir"),
    path("identidad", UpdateIdentidadView.as_view(), name="modulo0-identidad"),
    path("identidad/sugerir-ia", SugerirIdentidadIAView.as_view(), name="modulo0-identidad-sugerir-ia"),
    path("transicion-capitulo", TransicionCapituloView.as_view(), name="modulo0-transicion-capitulo"),
    path("historial-transiciones", HistorialTransicionesCapituloView.as_view(), name="modulo0-historial-transiciones"),
]

