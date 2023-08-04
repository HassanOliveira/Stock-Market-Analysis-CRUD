from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('registro/', views.registro, name='registro'),  # URL para a view de registro
    path('login/', auth_views.LoginView.as_view(template_name='investimentos/login.html'), name='login'),  # URL para a view de login
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),  # Adicione esta linha para a view de logout

    # Restante das URLs existentes
    path('', views.index, name='index'),
    path('monitorar_ativos/', views.monitorar_ativos, name='monitorar_ativos'),
    path('consultar_ativos/', views.consultar_ativos, name='consultar_ativos'),
    path('salvar_ativo/', views.salvar_ativo, name='salvar_ativo'),
    path('remover_ativo/<int:configuracao_id>/', views.remover_ativo, name='remover_ativo'),
]
