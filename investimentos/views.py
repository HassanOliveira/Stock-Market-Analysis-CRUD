from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage
from django.contrib.auth.decorators import login_required
from io import BytesIO
from .models import Ativos, ConfiguracaoAtivo, Cotacao
from .utils import salvando_codigos_ativos, processar_ativo, remove_indexes_with_prefix
from .notices import get_news, get_news_individual
from .tasks import agendar_tarefa_periodica, cancelar_tarefa
from .forms import RegistroForm
import matplotlib.pyplot as plt
import base64
import matplotlib

matplotlib.use("Agg")


# Página de registro.
def registro(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("index")
    else:
        form = RegistroForm()

    return render(request, "investimentos/registro.html", {"form": form})


# Página home com as noticias retiradas em tempo real do site da UOL.
@login_required
def index(request):
    user = request.user
    news_dict = get_news()

    context = {"user": user, "news_dict": news_dict}

    return render(request, "investimentos/index.html", context)


# Página da notícia acessada pelo usuário.
@login_required
def noticia_individual(request, noticia_url):
    news = get_news_individual(noticia_url)

    context = {"noticia_url": noticia_url, "news": news}

    return render(request, "investimentos/noticia.html", context)


# Página monitorar.
@login_required
def monitorar_ativos(request):
    try:
        configuracoes = ConfiguracaoAtivo.objects.filter(user=request.user).order_by(
            "-ativo"
        )
        codigos = sorted(salvando_codigos_ativos())

        ativos_por_pagina = 5

        paginator = Paginator(configuracoes, ativos_por_pagina)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        latest_cotacoes = []

        for config in page_obj:
            ativo = Ativos.objects.get(symbol=config.symbol, user=request.user)
            latest_cotacao = (
                Cotacao.objects.filter(ativo=ativo)
                .order_by("-regularMarketTime")
                .first()
            )
            latest_cotacoes.append(latest_cotacao)

        return render(
            request,
            "investimentos/monitorar_ativos.html",
            {
                "configuracoes": page_obj,
                "latest_cotacoes": latest_cotacoes,
                "codigos": codigos,
            },
        )

    except Exception as e:
        print(f"Erro ao monitorar ativos: {type(e)} - {e}")


# Função para salvar o monitoramento do ativo.
@login_required
def salvar_ativo(request):
    try:
        if request.method == "POST":
            user = request.user
            symbol = request.POST["ativo"]
            limite_inferior = request.POST["limite_inferior"]
            limite_superior = request.POST["limite_superior"]
            periodicidade = request.POST["periodicidade"]

            periodicidade = int(periodicidade)
            segundos = periodicidade * 60

            remove_indexes_with_prefix(
                "INOAinvestimentos",
                "investimentos_configuracaoativo",
                "investimentos_configuracaoativo_symbol",
            )

            processar_ativo(user, symbol, limite_inferior, limite_superior)

            # Agende a tarefa com o intervalo especificado
            agendar_tarefa_periodica(
                user, symbol, limite_inferior, limite_superior, segundos
            )

            # Redireciona para a página de monitorar ativos
            return redirect("monitorar_ativos")

    except Exception as e:
        print(f"Erro ao salvar ativo: {type(e)} - {e}")


# Função para remover o monitoramento do ativo.
@login_required
def remover_ativo(request, configuracao_id):
    try:
        configuracao = ConfiguracaoAtivo.objects.get(id=configuracao_id)
        cancelar_tarefa(configuracao.user, configuracao.symbol)
        configuracao.delete()
        return redirect("monitorar_ativos")
    except ConfiguracaoAtivo.DoesNotExist:
        messages.error(request, "Configuração de ativo não encontrada.")
        return redirect("monitorar_ativos")


# Página consultar.
@login_required
def consultar_ativos(request):
    search_query = request.GET.get("ativo_search")
    page_number = request.GET.get("page", 1)

    if search_query:
        cotacoes = Cotacao.objects.filter(user=request.user, symbol=search_query)
    else:
        cotacoes = []

    # Filtrar cotações e pegar o último valor de cada dia
    filtered_cotacoes = {}
    for cotacao in cotacoes:
        cotacao_date = cotacao.regularMarketTime.date()
        if cotacao_date not in filtered_cotacoes:
            filtered_cotacoes[cotacao_date] = cotacao
        elif (
            cotacao.regularMarketTime
            > filtered_cotacoes[cotacao_date].regularMarketTime
        ):
            filtered_cotacoes[cotacao_date] = cotacao

    paginator = Paginator(list(filtered_cotacoes.values()), 10)

    try:
        page_cotacoes = paginator.page(page_number)
    except EmptyPage:
        page_cotacoes = paginator.page(paginator.num_pages)

    # Converter cotações filtradas para listas de valores
    datas = list(filtered_cotacoes.keys())
    precos = [
        float(str(cotacao.regularMarketPrice)) for cotacao in filtered_cotacoes.values()
    ]

    plt.figure(figsize=(8, 5))
    plt.plot(datas, precos, marker="o")
    plt.title(f"Gráfico de Preço X Data para {search_query}")
    plt.xlabel("Data")
    plt.ylabel("Preço")
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.gca().set_facecolor("none")

    buffer = BytesIO()
    plt.savefig(buffer, format="png", transparent=True)
    plt.close()
    buffer.seek(0)

    grafico_base64 = base64.b64encode(buffer.getvalue()).decode()

    context = {
        "search_results": page_cotacoes,
        "grafico_base64": grafico_base64,
    }

    return render(request, "investimentos/consultar_ativos.html", context)
