from django.shortcuts import redirect
from .utils import (
    obter_dados_ativos,
    conexao_db,
    salvar_dados_BD,
    configuracao_ativo,
)

import schedule
import threading
import time

agendamentos = {}

# Função para processar o ativo
def processar_ativo(user, symbol, limite_inferior, limite_superior):
    try:
        with conexao_db() as client:
            dados = obter_dados_ativos(symbol)

            if dados is not None:
                salvar_dados_BD(dados, user)

                configuracao_ativo(user, symbol, limite_inferior, limite_superior)

    except Exception as e:
        print(f"Erro ao processar ativo: {type(e)} - {e}")


# Função para agendar a tarefa para um ativo com intervalo personalizado
def agendar_tarefa_periodica(user, symbol, limite_inferior, limite_superior, segundos):
    try:
        if user not in agendamentos:
            agendamentos[user] = {}

        cancelar_tarefa(user, symbol)

        # Agende uma nova tarefa com os dados atualizados
        job = schedule.every(segundos).seconds.do(
            processar_ativo, user, symbol, limite_inferior, limite_superior
        )
        agendamentos[user][symbol] = job

    except Exception as e:
        print(f"Erro ao agendar tarefa: {type(e)} - {e}")


def cancelar_tarefa(user, symbol):
    try:
        if user in agendamentos:
            if symbol in agendamentos[user]:
                # Se já existe uma tarefa agendada com o mesmo símbolo para o usuário, cancele-a
                job = agendamentos[user][symbol]
                schedule.cancel_job(job)

    except Exception as e:
        print(f"Erro ao cancelar tarefa: {type(e)} - {e}")


# Função para iniciar o agendamento em segundo plano
def iniciar_agendamento():
    while True:
        schedule.run_pending()
        time.sleep(1)


# Inicie o agendamento em segundo plano em uma thread separada
agendamento_thread = threading.Thread(target=iniciar_agendamento)
agendamento_thread.start()
