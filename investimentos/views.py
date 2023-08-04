from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from .models import Ativos, ConfiguracaoAtivo, Cotacao
from .utils import (
    obter_dados_ativos,
    salvando_codigos_ativos,
    conexao_db,
    salvar_dados_BD,
    configuracao_ativo,
)
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.db.models import Subquery, OuterRef
from .forms import RegistroForm


def registro(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(
                "index"
            )  # redirecione para a página inicial após o registro
    else:
        form = RegistroForm()
    return render(request, "investimentos/registro.html", {"form": form})


@login_required
def index(request):
    return render(request, "investimentos/index.html")


@login_required
def monitorar_ativos(request):
    configuracoes = ConfiguracaoAtivo.objects.all()

    latest_cotacoes = []

    for config in configuracoes:
        ativo = Ativos.objects.get(symbol=config.symbol)
        latest_cotacao = Cotacao.objects.filter(ativo=ativo).order_by('-regularMarketTime').first()
        latest_cotacoes.append(latest_cotacao)

    return render(
        request, "investimentos/monitorar_ativos.html", {"configuracoes": configuracoes, "latest_cotacoes": latest_cotacoes}
    )


@login_required
def consultar_ativos(request):
    configuracoes = ConfiguracaoAtivo.objects.filter(user=request.user)
    ativos_symbols = [config.symbol for config in configuracoes]
    
    latest_cotacoes = []

    for symbol in ativos_symbols:
        ativo = Ativos.objects.get(symbol=symbol)
        latest_cotacao = Cotacao.objects.filter(ativo=ativo).order_by('-regularMarketTime').first()
        latest_cotacoes.append(latest_cotacao)

    return render(request, "investimentos/consultar_ativos.html", {"latest_cotacoes": latest_cotacoes})


@login_required
def salvar_ativo(request):
    if request.method == "POST":
        codigo = request.POST["ativo"]
        limite_inferior = request.POST["limite_inferior"]
        limite_superior = request.POST["limite_superior"]
        # Estabelece a conexão com o banco de dados
        client = conexao_db()

        # Obtém os dados do ativo
        dados = obter_dados_ativos(codigo)

        if dados is not None:
            # Salva os dados no banco de dados
            salvar_dados_BD(dados, request.user)

            # Salva a configuração do ativo
            configuracao_ativo(request.user, codigo, limite_inferior, limite_superior)

            # Fecha a conexão com o banco de dados
            client.close()

            # Redireciona para a página de monitorar ativos
            return redirect("monitorar_ativos")

    return render(request, "investimentos/salvar_ativo.html")


@login_required
def remover_ativo(request, configuracao_id):
    try:
        configuracao = ConfiguracaoAtivo.objects.get(id=configuracao_id)
        configuracao.delete()
        return redirect("monitorar_ativos")
    except ConfiguracaoAtivo.DoesNotExist:
        messages.error(request, "Configuração de ativo não encontrada.")
        return redirect("monitorar_ativos")
