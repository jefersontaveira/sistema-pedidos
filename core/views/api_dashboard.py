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

    pedidos_hoje = Pedido.objects.filter(loja=loja, data_hora_pedido__date=hoje)

    # 1. Resumo Financeiro (esta lógica permanece a mesma)
    resumo = pedidos_hoje.aggregate(
        faturamento_diario=Coalesce(Sum('total'), Decimal('0.0')),
        pedidos_count=Count('id')
    )
    faturamento_diario = resumo['faturamento_diario']
    pedidos_count = resumo['pedidos_count']
    ticket_medio = faturamento_diario / pedidos_count if pedidos_count > 0 else Decimal('0.0')

    # 2. Forma de pagamento mais comum (lógica similar)
    pagamentos = pedidos_hoje.values('forma_pagamento__nome').annotate(count=Count('id')).order_by('-count')
    pagamento_mais_usado = pagamentos.first() if pagamentos else None

    # 3. Produtos mais vendidos (LÓGICA ATUALIZADA)
    contador_produtos = Counter()
    # Usamos prefetch_related para otimizar a busca e evitar múltiplas consultas ao banco
    for pedido in pedidos_hoje.prefetch_related('itens__produtos'):
        for item in pedido.itens.all():  # Itera sobre cada 'ItemPedido'
            for produto in item.produtos.all():  # Itera sobre cada 'Produto' dentro do item
                contador_produtos[produto.nome] += 1
    produtos_mais_vendidos = [{'nome': item, 'count': count} for item, count in contador_produtos.most_common(5)]

    # 4. Status dos pedidos (lógica permanece a mesma)
    status_pedidos = pedidos_hoje.exclude(status__in=['entregue', 'cancelado']).values('status').annotate(
        count=Count('id'))
    contagem_status = {item['status']: item['count'] for item in status_pedidos}

    # Monta o pacote de dados final para enviar ao JavaScript
    data = {
        'faturamento_diario': f'{faturamento_diario:.2f}'.replace('.', ','),
        'ticket_medio': f'{ticket_medio:.2f}'.replace('.', ','),
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
