from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage
from django.contrib.auth.decorators import login_required
from io import BytesIO
from .models import Ativos, ConfiguracaoAtivo, Cotacao
from .utils import saving_assets_codes, process_asset, remove_indexes_with_prefix
from .notices import get_news, get_news_individual
from .tasks import schedule_periodic_task, cancel_task
from .forms import RegistroForm
import matplotlib.pyplot as plt
import base64
import matplotlib

matplotlib.use("Agg")


# Página de registro.
def register(request):
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
def news_individual(request, noticia_url):
    news = get_news_individual(noticia_url)

    context = {"noticia_url": noticia_url, "news": news}

    return render(request, "investimentos/noticia.html", context)


# Página monitorar.
@login_required
def asset_monitor(request):
    try:
        configs = ConfiguracaoAtivo.objects.filter(user=request.user).order_by(
            "-asset"
        )
        codes = sorted(saving_assets_codes())

        asset_per_page = 5

        paginator = Paginator(configs, asset_per_page)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        latest_quotations = []

        for config in page_obj:
            asset = Ativos.objects.get(symbol=config.symbol, user=request.user)
            latest_quotation = (
                Cotacao.objects.filter(asset=asset)
                .order_by("-regularMarketTime")
                .first()
            )
            latest_quotations.append(latest_quotation)

        return render(
            request,
            "investimentos/monitorar_ativos.html",
            {
                "configs": page_obj,
                "latest_quotations": latest_quotations,
                "codes": codes,
            },
        )

    except Exception as e:
        print(f"Erro ao monitorar ativos: {type(e)} - {e}")


# Função para salvar o monitoramento do ativo.
@login_required
def save_asset(request):
    try:
        if request.method == "POST":
            user = request.user
            symbol = request.POST["asset"]
            lower_limit = request.POST["lower_limit"]
            upper_limit = request.POST["upper_limit"]
            periodicity = request.POST["periodicity"]

            periodicity = int(periodicity)
            seconds = periodicity * 60

            remove_indexes_with_prefix(
                "INOAinvestimentos",
                "investimentos_configuracaoativo",
                "investimentos_configuracaoativo_symbol",
            )

            process_asset(user, symbol, lower_limit, upper_limit)

            # Agende a tarefa com o intervalo especificado
            schedule_periodic_task(
                user, symbol, lower_limit, upper_limit, seconds
            )

            # Redireciona para a página de monitorar ativos
            return redirect("monitorar_ativos")

    except Exception as e:
        print(f"Erro ao salvar ativo: {type(e)} - {e}")


# Função para remover o monitoramento do ativo.
@login_required
def remove_asset(request, configuracao_id):
    try:
        config = ConfiguracaoAtivo.objects.get(id=configuracao_id)
        cancel_task(config.user, config.symbol)
        config.delete()
        return redirect("monitorar_ativos")
    except ConfiguracaoAtivo.DoesNotExist:
        messages.error(request, "Configuração de ativo não encontrada.")
        return redirect("monitorar_ativos")


# Página consultar.
@login_required
def consult_assets(request):
    search_query = request.GET.get("asset_search")
    page_number = request.GET.get("page", 1)

    if search_query:
        quotations = Cotacao.objects.filter(user=request.user, symbol=search_query)
    else:
        quotations = []

    # Filtrar cotações e pegar o último valor de cada dia
    filtered_quotations = {}
    for quotation in quotations:
        quotation_date = quotation.regularMarketTime.date()
        if quotation_date not in filtered_quotations:
            filtered_quotations[quotation_date] = quotation
        elif (
            quotation.regularMarketTime
            > filtered_quotations[quotation_date].regularMarketTime
        ):
            filtered_quotations[quotation_date] = quotation

    paginator = Paginator(list(filtered_quotations.values()), 10)

    try:
        page_quotations = paginator.page(page_number)
    except EmptyPage:
        page_quotations = paginator.page(paginator.num_pages)

    # Converter cotações filtradas para listas de valores
    datas = list(filtered_quotations.keys())
    prices = [
        float(str(quotation.regularMarketPrice)) for quotation in filtered_quotations.values()
    ]

    plt.figure(figsize=(8, 5))
    plt.plot(datas, prices, marker="o")
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

    graph_base64 = base64.b64encode(buffer.getvalue()).decode()

    context = {
        "search_results": page_quotations,
        "graph_base64": graph_base64,
    }

    return render(request, "investimentos/consultar_ativos.html", context)
