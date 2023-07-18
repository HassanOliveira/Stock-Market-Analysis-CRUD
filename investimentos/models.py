from django.db import models
from decimal import Decimal
from bson import ObjectId


class Cotacao(models.Model):
    ativo = models.ForeignKey('Ativos', on_delete=models.CASCADE)
    symbol = models.CharField(max_length=6)
    currency = models.CharField(max_length=10)
    regularMarketPrice = models.DecimalField(max_digits=10, decimal_places=2)
    regularMarketDayHigh = models.DecimalField(max_digits=10, decimal_places=2)
    regularMarketDayLow = models.DecimalField(max_digits=10, decimal_places=2)
    regularMarketTime = models.DateTimeField()

class Ativos(models.Model):
    symbol = models.CharField(max_length=6)
    nome = models.CharField(max_length=100)
    moeda = models.CharField(max_length=10)
    cotacoes = models.ManyToManyField(Cotacao)
    data_atualizacao = models.DateTimeField()

class ConfiguracaoAtivo(models.Model):
    ativo = models.OneToOneField(Ativos, on_delete=models.CASCADE)
    symbol = models.CharField(max_length=6)
    limite_inferior = models.DecimalField(max_digits=10, decimal_places=2)
    limite_superior = models.DecimalField(max_digits=10, decimal_places=2)

class Sugestoes(models.Model):
    symbol = models.CharField(max_length=50)
    tipo = models.CharField(max_length=10)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    data_hora_sugestao = models.DateTimeField()

