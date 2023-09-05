from django.utils import timezone
from email.mime.text import MIMEText
from decimal import Decimal
from .models import Ativos, Cotacao, ConfiguracaoAtivo
import smtplib
import requests
import pymongo
import decimal


def conexao_db():
    try:
        client = pymongo.MongoClient("localhost", 27017)
        return client

    except Exception as e:
        print(f"Erro ao estabelecer conexão com o banco de dados: {type(e)} - {e}")
        return None


# Obtem os dados e cotações do ativo informado pelo usuário.
def obter_dados_ativos(codigo):
    try:
        url = "https://brapi.dev/api/quote/{}?range=1d&interval=1d&fundamental=true&dividends=false".format(
            codigo
        )
        response = requests.get(url)

        response.raise_for_status()

        dados = response.json()
        return dados

    except requests.exceptions.RequestException as e:
        print(f"Erro de solicitação: {e}")
        return None

    except Exception as e:
        print(f"Erro ao obter dados ativos: {type(e)} - {e}")
        return None


# Salva as informações do ativo e suas cotações no banco de dados.
def salvar_dados_BD(dados, user):
    try:
        resultado = dados["results"][0]
        symbol = resultado["symbol"]

        if "longName" in resultado:
            longName = resultado["longName"]
        else:
            longName = None

        currency = resultado["currency"]
        regularMarketPrice = Decimal(resultado["regularMarketPrice"])
        regularMarketDayHigh = Decimal(resultado["regularMarketDayHigh"])
        regularMarketDayLow = Decimal(resultado["regularMarketDayLow"])
        regularMarketTime = timezone.now()

        # Verificar se o ativo já existe com um usuário diferente
        ativo_existente = Ativos.objects.filter(symbol=symbol, user=user).first()

        if not ativo_existente:
            # Caso contrário, crie um novo objeto Ativos com o user_id
            ativo = Ativos.objects.create(
                user=user,
                symbol=symbol,
                nome=longName,
                moeda=currency,
                data_atualizacao=regularMarketTime,
            )
        else:
            ativo = ativo_existente

        ativo.save()

        # Criar a instância de Cotacao
        cotacao = Cotacao.objects.create(
            user=user,
            ativo=ativo,
            symbol=symbol,
            currency=currency,
            regularMarketPrice=regularMarketPrice,
            regularMarketDayHigh=regularMarketDayHigh,
            regularMarketDayLow=regularMarketDayLow,
            regularMarketTime=regularMarketTime,
        )

        return regularMarketPrice

    except Exception as e:
        print(f"Erro ao salvar dados no banco de dados: {type(e)} - {e}")
        return None


# Salva as configurações de monitoramento do ativo.
def configuracao_ativo(user, symbol, limite_inferior, limite_superior):
    try:
        # Tenta obter a configuração existente com o mesmo símbolo e usuário
        configuracao = ConfiguracaoAtivo.objects.get(user=user, symbol=symbol)
        # Atualiza os limites inferiores e superiores da configuração existente
        configuracao.limite_inferior = limite_inferior
        configuracao.limite_superior = limite_superior
        configuracao.save()
    except ConfiguracaoAtivo.DoesNotExist:
        # Obtenha a instância de Ativos correspondente ao símbolo
        ativo = Ativos.objects.get(symbol=symbol, user=user)
        # Crie uma nova configuração associada ao ativo obtido
        configuracao = ConfiguracaoAtivo.objects.create(
            user=user,
            ativo=ativo,
            symbol=symbol,
            limite_inferior=limite_inferior,
            limite_superior=limite_superior,
        )
    except Exception as e:
        print(f"Erro durante a operação de configuração: {type(e)} - {e}")


# Salva os códigos dos ativos (ações).
def salvando_codigos_ativos():
    try:
        api_url = "https://brapi.dev/api/available"
        response = requests.get(api_url)

        response.raise_for_status()

        data = response.json()

        indices = data["indexes"]
        stocks = data["stocks"]

        codigos = indices + stocks
        return codigos

    except requests.exceptions.RequestException as e:
        print(f"Erro de solicitação: {e}")
        return None

    except Exception as e:
        print(f"Erro ao obter códigos de ativos: {type(e)} - {e}")
        return None


# Função para enviar e-mail.
def enviar_email(destinatario, assunto, mensagem):
    remetente = "emai@gmail.com"  # Substitua pelo seu endereço de e-mail
    senha = "1234"  # Substitua pela senha do seu e-mail

    # Configurar o servidor SMTP
    servidor_smtp = (
        "smtp.centrale-med.fr"  # Substitua pelo servidor SMTP do seu provedor de e-mail
    )
    porta_smtp = 587  # Ajuste para o seu provedor

    msg = MIMEText(
        f"""
        <html>
        <head>
            <style>
                /* Estilos CSS inline */
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f7f9;
                }}
                .container {{
                    padding: 20px;
                    background-color: #ffffff;
                    border: 1px solid #e0e6ed;
                }}
                h1 {{
                    color: #e74c3c;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{assunto}</h1>
                <p>{mensagem}</p>
            </div>
        </body>
        </html>
        """,
        "html",
    )
    msg["From"] = "Hassan BITTENCOURT"  # Seu nome
    msg["To"] = destinatario
    msg["Subject"] = assunto

    try:
        servidor = smtplib.SMTP(servidor_smtp, porta_smtp)

        servidor.starttls()

        servidor.login(remetente, senha)

        servidor.sendmail(remetente, destinatario, msg.as_string())

        servidor.quit()

        print("E-mail enviado com sucesso!")

    except Exception as e:
        print(f"Erro ao enviar e-mail: {str(e)}")


# Obtem nova cotação, salva no banco de dados e compara com os limites impostos pelo usuário.
def processar_ativo(user, symbol, limite_inferior, limite_superior):
    try:
        with conexao_db() as client:
            dados = obter_dados_ativos(symbol)

            if dados is not None:
                price = salvar_dados_BD(dados, user)

                limite_inferior_decimal = decimal.Decimal(limite_inferior)
                limite_superior_decimal = decimal.Decimal(limite_superior)

                if price < limite_inferior_decimal:
                    enviar_email(
                        user.email,
                        f"COMPRE O ATIVO {symbol}!",
                        f"É uma boa hora para comprar o ativo {symbol}.",
                    )
                elif price > limite_superior_decimal:
                    enviar_email(
                        user.email,
                        f"VENDA O ATIVO {symbol}!",
                        f"É uma boa hora para vender o ativo {symbol}.",
                    )

                configuracao_ativo(user, symbol, limite_inferior, limite_superior)

    except Exception as e:
        print(f"Erro ao processar ativo: {type(e)} - {e}")


# Função para resolver problema com indexes criados automaticamente pelo MongoDB.
def remove_indexes_with_prefix(database_name, collection_name, prefix):
    try:
        client = conexao_db()
        db = client[database_name]
        collection = db[collection_name]

        indexes = collection.list_indexes()

        for index in indexes:
            index_name = index["name"]
            if index_name.startswith(prefix):
                collection.drop_index(index_name)

    except Exception as e:
        print(f"Erro ao remover índices com prefixo: {type(e)} - {e}")
