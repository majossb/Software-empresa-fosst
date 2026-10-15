from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [

    # Registro
    path("registro/", views.RegistroView.as_view(), name="auth-registro"),
    path("activar/", views.ActivarCuentaView.as_view(), name="auth-activar"),

    # Login
    path("login/", views.LoginView.as_view(), name="auth-login"),
    path("verificar-otp/", views.VerificarOTPView.as_view(), name="auth-verificar-otp"),
    path("logout/", views.LogoutView.as_view(), name="auth-logout"),
    path("me/", views.MeView.as_view(), name="auth-me"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    # Password
    path(
        "password/solicitar-reset/",
        views.SolicitarResetPasswordView.as_view(),
        name="password-solicitar-reset",
    ),
    path(
        "password/confirmar-reset/",
        views.ConfirmarResetPasswordView.as_view(),
        name="password-confirmar-reset",
    ),
]