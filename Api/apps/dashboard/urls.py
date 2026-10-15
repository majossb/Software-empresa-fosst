from django.urls import path
from .views import (
    DashboardAltaDireccionView,
    DashboardResponsableView,
    DashboardAuditorView,
)

urlpatterns = [
    path("alta-direccion", DashboardAltaDireccionView.as_view(), name="dashboard-alta-direccion"),
    path("responsable", DashboardResponsableView.as_view(), name="dashboard-responsable"),
    path("auditor", DashboardAuditorView.as_view(), name="dashboard-auditor"),
]
