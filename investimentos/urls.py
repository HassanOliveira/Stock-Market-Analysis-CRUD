from django.urls import path
from investimentos import views

urlpatterns = [
    path('', views.index, name='index'),
    path('monitorar_ativos/', views.monitorar_ativos, name='monitorar_ativos'),
    path('consultar_ativos/', views.consultar_ativos, name='consultar_ativos'),
    path('salvar_ativo', views.salvar_ativo, name='salvar_ativo'),
    path('remover_ativo/<int:configuracao_id>/', views.remover_ativo, name='remover_ativo'),
]