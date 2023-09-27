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
def get_active_data(code):
    try:
        url = "https://brapi.dev/api/quote/{}?token=cZJPm1YL52GCR59NJebeS2&range=1d&interval=1d&fundamental=true&dividends=false".format(
            code
        )
        response = requests.get(url)

        response.raise_for_status()

        datas = response.json()
        return datas

    except requests.exceptions.RequestException as e:
        print(f"Erro de solicitação: {e}")
        return None

    except Exception as e:
        print(f"Erro ao obter dados ativos: {type(e)} - {e}")
        return None


# Salva as informações do ativo e suas cotações no banco de dados.
def save_data_BD(datas, user):
    try:
        result = datas["results"][0]
        symbol = result["symbol"]

        if "longName" in result:
            longName = result["longName"]
        else:
            longName = None

        currency = result["currency"]
        regularMarketPrice = Decimal(result["regularMarketPrice"])
        regularMarketDayHigh = Decimal(result["regularMarketDayHigh"])
        regularMarketDayLow = Decimal(result["regularMarketDayLow"])
        regularMarketTime = timezone.now()

        # Verificar se o ativo já existe com um usuário diferente
        existing_asset = Ativos.objects.filter(symbol=symbol, user=user).first()

        if not existing_asset:
            # Caso contrário, crie um novo objeto Ativos com o user_id
            asset = Ativos.objects.create(
                user=user,
                symbol=symbol,
                name=longName,
                currency=currency,
                update_date=regularMarketTime,
            )
        else:
            asset = existing_asset

        asset.save()

        # Criar a instância de Cotacao
        quotation = Cotacao.objects.create(
            user=user,
            asset=asset,
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
def asset_configuration(user, symbol, lower_limit, upper_limit):
    try:
        # Tenta obter a configuração existente com o mesmo símbolo e usuário
        config = ConfiguracaoAtivo.objects.get(user=user, symbol=symbol)
        # Atualiza os limites inferiores e superiores da configuração existente
        config.lower_limit = lower_limit
        config.upper_limit = upper_limit
        config.save()
    except ConfiguracaoAtivo.DoesNotExist:
        # Obtenha a instância de Ativos correspondente ao símbolo
        asset = Ativos.objects.get(symbol=symbol, user=user)
        # Crie uma nova configuração associada ao ativo obtido
        config = ConfiguracaoAtivo.objects.create(
            user=user,
            asset=asset,
            symbol=symbol,
            lower_limit=lower_limit,
            upper_limit=upper_limit,
        )
    except Exception as e:
        print(f"Erro durante a operação de configuração: {type(e)} - {e}")


# Salva os códigos dos ativos (ações).
def saving_assets_codes():
    try:
        api_url = "https://brapi.dev/api/available"
        response = requests.get(api_url)

        response.raise_for_status()

        data = response.json()

        indices = data["indexes"]
        stocks = data["stocks"]

        codes = indices + stocks
        return codes

    except requests.exceptions.RequestException as e:
        print(f"Erro de solicitação: {e}")
        return None

    except Exception as e:
        print(f"Erro ao obter códigos de ativos: {type(e)} - {e}")
        return None


# Função para enviar e-mail.
def enviar_email(destinatario, assunto, mensagem):
    sender = "emai@gmail.com"  # Substitua pelo seu endereço de e-mail
    password = "1234"  # Substitua pela senha do seu e-mail

    # Configurar o servidor SMTP
    server_smtp = (
        "smtp.centrale-med.fr"  # Substitua pelo servidor SMTP do seu provedor de e-mail
    )
    port_smtp = 587  # Ajuste para o seu provedor

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
        server = smtplib.SMTP(server_smtp, port_smtp)

        server.starttls()

        server.login(sender, password)

        server.sendmail(sender, destinatario, msg.as_string())

        server.quit()

        print("E-mail enviado com sucesso!")

    except Exception as e:
        print(f"Erro ao enviar e-mail: {str(e)}")


# Obtem nova cotação, salva no banco de dados e compara com os limites impostos pelo usuário.
def process_asset(user, symbol, lower_limit, upper_limit):
    try:
        with conexao_db() as client:
            datas = get_active_data(symbol)

            if datas is not None:
                price = save_data_BD(datas, user)

                lower_limit_decimal = decimal.Decimal(lower_limit)
                upper_limit_decimal = decimal.Decimal(upper_limit)

                if price < lower_limit_decimal:
                    enviar_email(
                        user.email,
                        f"COMPRE O ATIVO {symbol}!",
                        f"É uma boa hora para comprar o ativo {symbol}.",
                    )
                elif price > upper_limit_decimal:
                    enviar_email(
                        user.email,
                        f"VENDA O ATIVO {symbol}!",
                        f"É uma boa hora para vender o ativo {symbol}.",
                    )

                asset_configuration(user, symbol, lower_limit, upper_limit)

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
