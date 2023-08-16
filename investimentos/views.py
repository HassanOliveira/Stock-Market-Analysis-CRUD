from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage
from .models import Ativos, ConfiguracaoAtivo, Cotacao
from .utils import (
    obter_dados_ativos,
    conexao_db,
    salvar_dados_BD,
    configuracao_ativo,
)
from django.contrib.auth.decorators import login_required
from .forms import RegistroForm
from io import BytesIO
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


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
    user = request.user
    context = {"user": user}
    return render(request, "investimentos/index.html", context)


@login_required
def monitorar_ativos(request):
    configuracoes = ConfiguracaoAtivo.objects.filter(user=request.user)

    latest_cotacoes = []

    for config in configuracoes:
        ativo = Ativos.objects.get(symbol=config.symbol)
        latest_cotacao = Cotacao.objects.filter(ativo=ativo).order_by('-regularMarketTime').first()
        latest_cotacoes.append(latest_cotacao)

    return render(
        request, "investimentos/monitorar_ativos.html", {"configuracoes": configuracoes, "latest_cotacoes": latest_cotacoes}
    )



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
    

@login_required
def consultar_ativos(request):
    search_query = request.GET.get('ativo_search')
    page_number = request.GET.get('page', 1)  # Número da página (padrão: 1)

    if search_query:
        cotacoes = Cotacao.objects.filter(user=request.user, symbol=search_query).order_by('-regularMarketTime')
    else:
        cotacoes = []

    paginator = Paginator(cotacoes, 10)  # 15 cotações por página

    try:
        page_cotacoes = paginator.page(page_number)
    except EmptyPage:
        page_cotacoes = paginator.page(paginator.num_pages)  # Página inválida, vá para a última página

    # Converter cotações para listas de valores
    datas = [cotacao.regularMarketTime.date() for cotacao in cotacoes]
    precos = [float(str(cotacao.regularMarketPrice)) for cotacao in cotacoes]

    plt.figure(figsize=(8, 5))
    plt.plot(datas, precos, marker='o')
    plt.title(f'Gráfico de Preço X Data para {search_query}')
    plt.xlabel('Data')
    plt.ylabel('Preço')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Defina o fundo do gráfico como transparente
    plt.gca().set_facecolor('none')

    # Salvar o gráfico em um buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png', transparent=True)
    plt.close()
    buffer.seek(0)

    # Converter o buffer em base64 para exibir no template
    grafico_base64 = base64.b64encode(buffer.getvalue()).decode()

    context = {
        'search_results': page_cotacoes,
        'grafico_base64': grafico_base64,
    }

    return render(request, 'investimentos/consultar_ativos.html', context)