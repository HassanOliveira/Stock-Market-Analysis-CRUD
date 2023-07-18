from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Ativos, ConfiguracaoAtivo, Sugestoes
from .utils import obter_dados_ativos, salvando_codigos_ativos, conexao_db, salvar_dados_BD, configuracao_ativo
from django.core.exceptions import ObjectDoesNotExist



def index(request):
    return render(request, '../templates/investimentos/index.html')

def monitorar_ativos(request):
    configuracoes = ConfiguracaoAtivo.objects.all()
    return render(request, 'investimentos/monitorar_ativos.html', {'configuracoes': configuracoes})

def consultar_ativos(request):
    ativos = Ativos.objects.all()
    return render(request, '../templates/investimentos/consultar_ativos.html', {'ativos': ativos})


def salvar_ativo(request):
    if request.method == 'POST':
        codigo = request.POST['ativo']
        limite_inferior = request.POST['limite_inferior']
        limite_superior = request.POST['limite_superior']        
        # Estabelece a conexão com o banco de dados
        client = conexao_db()
        
        # Obtém os dados do ativo
        dados = obter_dados_ativos(codigo)

        if dados is not None:
            # Salva os dados no banco de dados
            salvar_dados_BD(dados)

            # Salva a configuração do ativo
            configuracao_ativo(codigo, limite_inferior, limite_superior)

            # Fecha a conexão com o banco de dados
            client.close()
            
            # Redireciona para a página de monitorar ativos
            return redirect('monitorar_ativos')
    
    return render(request, 'investimentos/salvar_ativo.html')


def remover_ativo(request, configuracao_id):
    try:
        configuracao = ConfiguracaoAtivo.objects.get(id=configuracao_id)
        configuracao.delete()
        return redirect('monitorar_ativos')
    except ConfiguracaoAtivo.DoesNotExist:
        messages.error(request, 'Configuração de ativo não encontrada.')
        return redirect('monitorar_ativos')
