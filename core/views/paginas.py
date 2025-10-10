# core/views/paginas.py

from django.shortcuts import render, get_object_or_404
from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required
from core.models import Loja, Categoria, Pedido, Produto, Entregador


def pagina_loja(request, slug_da_loja):
    """
    Busca uma loja pelo seu 'slug' e exibe seu cardápio,
    organizado por categorias e produtos.
    """
    loja = get_object_or_404(Loja, slug=slug_da_loja, ativa=True)
    produtos_disponiveis = Produto.objects.filter(disponivel=True)

    # Busca todas as categorias daquela loja e, de quebra, já busca
    # todos os produtos relacionados a elas de uma vez (por performance).
    categorias = Categoria.objects.filter(loja=loja, disponivel=True).prefetch_related('produtos')

    context = {
        'loja': loja,
        'categorias': categorias,
    }

    return render(request, 'core/pagina_loja.html', context)


@login_required
def admin_geral(request, loja_id):
    loja = get_object_or_404(Loja, id=loja_id)

    # Filtra os pedidos que NÃO estão como 'Entregue' para exibir no painel
    pedidos_ativos = Pedido.objects.filter(loja=loja).exclude(status__in=['entregue', 'cancelado']).order_by('data_hora_pedido')

    # Busca os entregadores no banco de dados
    entregadores_da_loja = Entregador.objects.filter(loja=loja)

    # Busca todas as categorias da loja e já "pré-carrega" os produtos de cada uma
    categorias_da_loja = Categoria.objects.filter(loja=loja).prefetch_related('produtos')

    context = {
        'loja': loja,
        'pedidos_recebidos': pedidos_ativos.filter(status='recebido'),
        'pedidos_em_preparo': pedidos_ativos.filter(status='em_preparo'),
        'pedidos_prontos': pedidos_ativos.filter(status='pronto'),
        'entregadores': entregadores_da_loja,
        'categorias': categorias_da_loja,
    }


    return render(request, 'core/admin_geral.html', context)

def painel_loja(request, loja_id):
    loja = get_object_or_404(Loja, id=loja_id)
    # Filtra os pedidos que NÃO estão como 'Entregue' para exibir no painel
    pedidos_ativos = Pedido.objects.filter(loja=loja).exclude(status='entregue').order_by('data_hora_pedido')

    context = {
        'loja': loja,
        'pedidos_recebidos': pedidos_ativos.filter(status='recebido'),
        'pedidos_em_preparo': pedidos_ativos.filter(status='em_preparo'),
        'pedidos_prontos': pedidos_ativos.filter(status='pronto'),
    }
    return render(request, 'core/painel_loja.html', context)