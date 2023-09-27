from django.shortcuts import redirect
from .utils import (
    get_active_data,
    conexao_db,
    save_data_BD,
    asset_configuration,
)

import schedule
import threading
import time

appointments = {}

# Função para processar o ativo
def process_asset(user, symbol, lower_limit, upper_limit):
    try:
        with conexao_db() as client:
            dados = get_active_data(symbol)

            if dados is not None:
                save_data_BD(dados, user)

                asset_configuration(user, symbol, lower_limit, upper_limit)

    except Exception as e:
        print(f"Erro ao processar ativo: {type(e)} - {e}")


# Função para agendar a tarefa para um ativo com intervalo personalizado
def schedule_periodic_task(user, symbol, lower_limit, upper_limit, seconds):
    try:
        if user not in appointments:
            appointments[user] = {}

        cancel_task(user, symbol)

        # Agende uma nova tarefa com os dados atualizados
        job = schedule.every(seconds).seconds.do(
            process_asset, user, symbol, lower_limit, upper_limit
        )
        appointments[user][symbol] = job

    except Exception as e:
        print(f"Erro ao agendar tarefa: {type(e)} - {e}")


def cancel_task(user, symbol):
    try:
        if user in appointments:
            if symbol in appointments[user]:
                # Se já existe uma tarefa agendada com o mesmo símbolo para o usuário, cancele-a
                job = appointments[user][symbol]
                schedule.cancel_job(job)

    except Exception as e:
        print(f"Erro ao cancelar tarefa: {type(e)} - {e}")


# Função para iniciar o agendamento em segundo plano
def start_scheduling():
    while True:
        schedule.run_pending()
        time.sleep(1)


# Inicie o agendamento em segundo plano em uma thread separada
appointment_thread = threading.Thread(target=start_scheduling)
appointment_thread.start()
