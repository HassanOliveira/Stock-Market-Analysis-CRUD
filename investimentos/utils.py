import requests, pymongo
from decimal import Decimal
from .models import Ativos, Cotacao, ConfiguracaoAtivo

def conexao_db():
    client = pymongo.MongoClient("localhost", 27017)
    database = client["INOAinvestimentos"]

    return client


def obter_dados_ativos(codigo):
    url = "https://brapi.dev/api/quote/{}?range=1d&interval=1d&fundamental=true&dividends=false".format(codigo)
    response = requests.get(url)
    if response.status_code == 200:
        dados = response.json()
        return dados
    else:
        return None


def salvar_dados_BD(dados):
    # Obter os dados do primeiro resultado
    resultado = dados["results"][0]
    symbol = resultado["symbol"]
    longName = resultado["longName"]
    currency = resultado["currency"]
    regularMarketPrice = Decimal(resultado["regularMarketPrice"])
    regularMarketDayHigh = Decimal(resultado["regularMarketDayHigh"])
    regularMarketDayLow = Decimal(resultado["regularMarketDayLow"])
    regularMarketTime = resultado["regularMarketTime"]

    # Criar ou atualizar o objeto Ativos
    ativo, created = Ativos.objects.update_or_create(
        symbol=symbol,
        defaults={
            "symbol": symbol,
            "nome": longName,
            "moeda": currency,
            "data_atualizacao": regularMarketTime
        }
    )

    # Criar a instância de Cotacao
    cotacao = Cotacao.objects.create(
        ativo=ativo,
        symbol=symbol,
        currency=currency,
        regularMarketPrice=regularMarketPrice,
        regularMarketDayHigh=regularMarketDayHigh,
        regularMarketDayLow=regularMarketDayLow,
        regularMarketTime=regularMarketTime
    )


def configuracao_ativo(codigo, limite_inferior, limite_superior):
    try:
        # Tenta obter a configuração existente com o mesmo símbolo
        configuracao = ConfiguracaoAtivo.objects.get(symbol=codigo)
        # Atualiza os limites inferiores e superiores da configuração existente
        configuracao.limite_inferior = limite_inferior
        configuracao.limite_superior = limite_superior
        configuracao.save()
    except ConfiguracaoAtivo.DoesNotExist:
        # Se não existir uma configuração com o mesmo símbolo, cria uma nova configuração
        configuracao = ConfiguracaoAtivo.objects.create(
            symbol=codigo,
            limite_inferior=limite_inferior,
            limite_superior=limite_superior
        )

# PROBLEMA AO SALVAR OUTRA CONFIGURAÇÃO DE ATIVO. VERIFICAR RELAÇÃO ENTRE MODELS ATIVO E CONFIGURACAOATIVO.


    

def salvando_codigos_ativos():
    api_url = "https://brapi.dev/api/available"
    response = requests.get(api_url)
    data = response.json()

    indices = data["indexes"]
    stocks = data["stocks"]

    codigos = indices + stocks
    return codigos