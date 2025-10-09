# core/views/api_dashboard.py

from decimal import Decimal
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Sum, Count, Max
from django.db.models.functions import Coalesce
from collections import Counter

from core.models import (
    Loja,
    AcessoLoja,
    Categoria,
    Produto,
    Pedido,
    FormaPagamento,
    Entregador,
    Cupom,
    ItemPedido
)


def dashboard_data(request, loja_id):
    loja = get_object_or_404(Loja, id=loja_id)
    hoje = timezone.now().date()

    # Filtra os pedidos da loja feitos hoje
    pedidos_hoje = Pedido.objects.filter(loja=loja, data_hora_pedido__date=hoje)

    # 1. Resumo Financeiro
    resumo = pedidos_hoje.aggregate(
        faturamento_diario=Coalesce(Sum('total'), Decimal('0.0')),
        pedidos_count=Count('id')
    )
    faturamento_diario = resumo['faturamento_diario']
    pedidos_count = resumo['pedidos_count']
    ticket_medio = faturamento_diario / pedidos_count if pedidos_count > 0 else Decimal('0.0')

    # 2. Forma de pagamento mais comum
    pagamentos = pedidos_hoje.values('forma_pagamento').annotate(count=Count('id')).order_by('-count')
    pagamento_mais_usado = pagamentos.first() if pagamentos else None

    # 3. Produtos mais vendidos (Sabores + Adicionais)
    contador_produtos = Counter()
    for pedido in pedidos_hoje:
        for sabor in pedido.sabores.all():
            contador_produtos[sabor.nome] += 1
        for adicional in pedido.adicionais.all():
            contador_produtos[adicional.nome] += 1
    produtos_mais_vendidos = [{'nome': item, 'count': count} for item, count in contador_produtos.most_common(5)]

    # 4. Status dos pedidos
    status_pedidos = pedidos_hoje.exclude(status='entregue').values('status').annotate(count=Count('id'))
    contagem_status = {item['status']: item['count'] for item in status_pedidos}

    data = {
        'faturamento_diario': f'{faturamento_diario:.2f}'.replace('.',','),
        'ticket_medio': f'{ticket_medio:.2f}'.replace('.',','),
        'pedidos_count': pedidos_count,
        'pagamento_mais_usado': pagamento_mais_usado,
        'produtos_mais_vendidos': produtos_mais_vendidos,
        'contagem_status': {
            'aguardando': contagem_status.get('recebido', 0),
            'em_preparo': contagem_status.get('em_preparo', 0),
            'pronto': contagem_status.get('pronto', 0),
        }
    }
    return JsonResponse(data)
