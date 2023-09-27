from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("registro/", views.register, name="registro"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="investimentos/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", views.index, name="index"),
    path("monitorar_ativos/", views.asset_monitor, name="monitorar_ativos"),
    path("consultar_ativos/", views.consult_assets, name="consultar_ativos"),
    path("salvar_ativo/", views.save_asset, name="salvar_ativo"),
    path(
        "remover_ativo/<int:configuracao_id>/",
        views.remove_asset,
        name="remover_ativo",
    ),
    path("noticia<path:noticia_url>/", views.news_individual, name="noticia"),
]
