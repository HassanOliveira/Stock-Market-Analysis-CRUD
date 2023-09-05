from django.db import models
from django.contrib.auth.models import User


# Estrutura do modelo Cotacao, onde contém as cotações dos ativos.
class Cotacao(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ativo = models.ForeignKey("Ativos", on_delete=models.CASCADE)
    symbol = models.CharField(max_length=6)
    currency = models.CharField(max_length=10)
    regularMarketPrice = models.DecimalField(max_digits=10, decimal_places=2)
    regularMarketDayHigh = models.DecimalField(max_digits=10, decimal_places=2)
    regularMarketDayLow = models.DecimalField(max_digits=10, decimal_places=2)
    regularMarketTime = models.DateTimeField()


# Estrutura do modelo Ativos, onde contém as informações dos ativos.
class Ativos(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    symbol = models.CharField(max_length=6)
    nome = models.CharField(max_length=100)
    moeda = models.CharField(max_length=10)
    cotacoes = models.ManyToManyField(Cotacao)
    data_atualizacao = models.DateTimeField()


# Estrutura do modelo ConfiguracaoAtivo, onde contém as configurações de monitoramento de cada ativo de cada usuário.
class ConfiguracaoAtivo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=False)
    ativo = models.ForeignKey(Ativos, on_delete=models.CASCADE)
    symbol = models.CharField(max_length=6, db_index=False)
    limite_inferior = models.DecimalField(max_digits=10, decimal_places=2)
    limite_superior = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.user} - {self.symbol}"
