# core/models.py

import uuid
from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.core.validators import MaxValueValidator, MinValueValidator


# ----------------------------------------
# MODELOS DE GESTÃO E ESTRUTURA
# ----------------------------------------

class Loja(models.Model):
    """Representa a loja de um cliente. O coração do modelo multi-loja."""
    slug = models.UUIDField(default=uuid.uuid4, editable=False, unique=True,
                            help_text="ID público e seguro para a URL da loja")
    nome = models.CharField(max_length=100, help_text="Nome fantasia do estabelecimento")
    cnpj = models.CharField(max_length=18, unique=True, help_text="CNPJ da loja (apenas números)")
    nome_proprietario = models.CharField(max_length=100, help_text="Nome completo do dono da loja")
    email = models.EmailField(max_length=100, help_text="Email de contato da loja")
    telefone = models.CharField(max_length=20, help_text="Telefone/WhatsApp de contato da loja")
    logotipo = models.ImageField(upload_to='logotipos/', blank=True, null=True)

    ativa = models.BooleanField(default=False, help_text="Interruptor geral. Se desmarcado, a loja fica offline.")
    valor_mensalidade = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    # Este campo substitui a data de vencimento fixa.
    dia_vencimento_mensalidade = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="O dia do mês para o vencimento da fatura (de 1 a 31).",
        null=True, blank=True
    )


class AcessoLoja(models.Model):
    """Tabela de permissão: conecta um Usuário a uma Loja com uma Função específica."""
    FUNCAO_CHOICES = [
        ('DONO', 'Dono'),
        ('ATENDENTE', 'Atendente'),
    ]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE)
    funcao = models.CharField(max_length=20, choices=FUNCAO_CHOICES)

    class Meta:
        unique_together = ('usuario', 'loja')  # Garante que um usuário só tenha uma função por loja

    def __str__(self):
        return f"{self.usuario.username} - {self.funcao} na {self.loja.nome}"


# ----------------------------------------
# MODELOS OPERACIONAIS DA LOJA
# ----------------------------------------

class FormaPagamento(models.Model):
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='formas_pagamento')
    nome = models.CharField(max_length=50)
    ativa = models.BooleanField(default=True)

    def __str__(self): return self.nome


class Entregador(models.Model):
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='entregadores')
    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self): return self.nome


class Cupom(models.Model):
    TIPO_CHOICES = [('PERCENTUAL', 'Percentual'), ('FIXO', 'Fixo')]
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='cupons')
    codigo = models.CharField(max_length=20, unique=True)
    descricao = models.CharField(max_length=255, blank=True, null=True)
    tipo_desconto = models.CharField(max_length=10, choices=TIPO_CHOICES)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    ativo = models.BooleanField(default=True)
    data_validade = models.DateField(null=True, blank=True)

    def __str__(self): return self.codigo


class Categoria(models.Model):
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='categorias')
    nome = models.CharField(max_length=100)
    ordem = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordem', 'nome']

    def __str__(self): return self.nome


class Produto(models.Model):
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='produtos')
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='produtos')
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    foto = models.ImageField(upload_to='produtos/', blank=True, null=True)
    disponivel = models.BooleanField(default=True)

    class Meta:
        ordering = ['nome']

    def __str__(self): return self.nome


# ----------------------------------------
# MODELO TRANSACIONAL
# ----------------------------------------

class ItemPedido(models.Model):
    """
    Representa um item montado dentro de um pedido.
    Ex: '1 Açaí 500ml com morango e granola'.
    """
    # Cada Item pertence a um Pedido. Se o Pedido for apagado, o item também é.
    pedido = models.ForeignKey('Pedido', on_delete=models.CASCADE, related_name='itens')

    # Cada Item é composto por vários Produtos (Tamanho, Adicionais, etc.)
    produtos = models.ManyToManyField(Produto)

    def __str__(self):
        return f"Item de Pedido ID: {self.id or 'Novo Item'}"


class Pedido(models.Model):
    STATUS_CHOICES = [('recebido', 'Recebido'), ('em_preparo', 'Em Preparo'), ('pronto', 'Pronto'),
                      ('entregue', 'Entregue'), ('cancelado', 'Cancelado')]

    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='pedidos')
    nome_cliente = models.CharField(max_length=100)
    telefone_cliente = models.CharField(max_length=20)
    endereco_rua = models.CharField(max_length=255, default='')
    endereco_numero = models.CharField(max_length=20, default='')
    endereco_bairro = models.CharField(max_length=100, default='')
    endereco_referencia = models.CharField(max_length=255, blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    troco_para = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='recebido')
    data_hora_pedido = models.DateTimeField(auto_now_add=True)
    forma_pagamento = models.ForeignKey(FormaPagamento, on_delete=models.SET_NULL, null=True, blank=True)
    entregador = models.ForeignKey(Entregador, on_delete=models.SET_NULL, null=True, blank=True)
    cupom = models.ForeignKey(Cupom, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Pedido #{self.id} - {self.nome_cliente}"