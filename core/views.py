# core/views.py



import json
from decimal import Decimal
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Sum, Count
from django.db.models.functions import Coalesce
from collections import Counter

from .models import (
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


def pagina_loja(request, slug_da_loja):
    """
    Busca uma loja pelo seu 'slug' e exibe seu cardápio,
    organizado por categorias e produtos.
    """
    loja = get_object_or_404(Loja, slug=slug_da_loja, ativa=True)

    # Busca todas as categorias daquela loja e, de quebra, já busca
    # todos os produtos relacionados a elas de uma vez (por performance).
    categorias = Categoria.objects.filter(loja=loja).prefetch_related('produtos')

    context = {
        'loja': loja,
        'categorias': categorias,
    }

    return render(request, 'core/pagina_loja.html', context)


@csrf_exempt
# Em core/views.py

@csrf_exempt
def finalizar_pedido(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            loja_id = data.get('loja_id')
            loja = Loja.objects.get(id=loja_id)
            cliente = data.get('cliente', {})
            carrinho_final_js = data.get('carrinho', [])

            if not carrinho_final_js:
                return JsonResponse({'success': False, 'error': 'O carrinho está vazio.'})

            total_pedido = Decimal(0)
            todos_produtos_ids = []
            for item_montado in carrinho_final_js:
                for produto in item_montado:
                    todos_produtos_ids.append(produto['id'])

            produtos_no_pedido = Produto.objects.filter(id__in=todos_produtos_ids)
            for produto in produtos_no_pedido:
                total_pedido += produto.preco

            forma_pagamento_str = cliente.get('pagamento')
            forma_pagamento_obj = FormaPagamento.objects.get(loja=loja, nome__iexact=forma_pagamento_str)

            novo_pedido = Pedido.objects.create(
                loja=loja,
                nome_cliente=cliente.get('nome'),
                telefone_cliente=cliente.get('telefone'),
                endereco_rua=cliente.get('rua'),
                endereco_numero=cliente.get('numero'),
                endereco_bairro=cliente.get('bairro'),
                endereco_referencia=cliente.get('referencia'),
                forma_pagamento=forma_pagamento_obj,
                observacoes=cliente.get('observacoes'),
                total=total_pedido
            )

            for item_montado in carrinho_final_js:
                novo_item_pedido = ItemPedido.objects.create(pedido=novo_pedido)
                ids_deste_item = [p['id'] for p in item_montado]
                produtos_deste_item = Produto.objects.filter(id__in=ids_deste_item)
                novo_item_pedido.produtos.set(produtos_deste_item)

            return JsonResponse({'success': True, 'pedido_id': novo_pedido.id})

        except Loja.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Loja não encontrada.'})
        except FormaPagamento.DoesNotExist:
            return JsonResponse(
                {'success': False, 'error': f'Forma de pagamento "{cliente.get("pagamento")}" não é válida.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método inválido'})


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

@csrf_exempt
def atualizar_disponibilidade(request):
    # Verifica se a requisição é do tipo POST
    if request.method == 'POST':
        try:
            # Carrega os dados enviados pelo JavaScript
            data = json.loads(request.body)
            produto_id = data.get('produto_id')
            tipo_produto = data.get('tipo_produto')
            disponivel = data.get('disponivel')

            # Mapeia o texto 'tipo_produto' para o Model Django correspondente
            model_map = {
                'tamanho': Tamanho,
                'sabor': Sabor,
                'adicional': Adicional
            }
            Model = model_map.get(tipo_produto)

            # Validação para garantir que os dados necessários foram recebidos
            if not all([Model, produto_id is not None, disponivel is not None]):
                return JsonResponse({'success': False, 'error': 'Dados inválidos'})

            # Busca o produto específico no banco de dados
            produto = Model.objects.get(id=produto_id)

            # Atualiza o campo 'disponivel' com o novo valor
            produto.disponivel = disponivel
            produto.save()

            # Retorna uma resposta de sucesso para o JavaScript
            return JsonResponse({'success': True, 'message': 'Status atualizado com sucesso!'})

        except Model.DoesNotExist:
             return JsonResponse({'success': False, 'error': 'Produto não encontrado'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método inválido'})

def serialize_produto(produto, tipo):
    """Função auxiliar para converter um objeto de produto em um dicionário."""
    data = {
        'id': produto.id,
        'nome': produto.nome,
        'disponivel': produto.disponivel
    }
    if tipo == 'tamanho':
        # Forçamos a conversão para Decimal antes de formatar
        data['preco_base'] = f'{Decimal(produto.preco_base):.2f}'
    elif tipo == 'adicional':
        # Forçamos a conversão para Decimal antes de formatar
        data['preco'] = f'{Decimal(produto.preco):.2f}'
    return data

@csrf_exempt
def adicionar_produto(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            loja_id = data.get('loja_id')
            tipo_produto = data.get('tipo_produto')
            nome = data.get('nome')

            # --- INÍCIO DO NOVO BLOCO DE VALIDAÇÃO DE PREÇO ---

            # 1. Pega o preço como veio do frontend (pode ser "10,00", "10.00", "", etc.)
            preco_str = data.get('preco')

            # 2. Verifica se o valor é nulo (None) ou uma string vazia. Se for, trata como 0.
            if not preco_str:
                preco_decimal = Decimal('0.00')
            else:
                # 3. Se não for vazio, preparamos a string para a conversão:
                #    - str(preco_str): Garante que estamos trabalhando com uma string.
                #    - .replace(',', '.'): A MÁGICA ACONTECE AQUI! Trocamos a vírgula por ponto.
                #    - .strip(): Remove espaços em branco extras no início ou fim.
                preco_formatado = str(preco_str).replace(',', '.').strip()

                # 4. Agora, convertemos a string limpa e formatada para o tipo Decimal.
                preco_decimal = Decimal(preco_formatado)

            # --- FIM DO NOVO BLOCO DE VALIDAÇÃO DE PREÇO ---

            loja = Loja.objects.get(id=loja_id)
            model_map = {'tamanho': Tamanho, 'sabor': Sabor, 'adicional': Adicional}
            Model = model_map.get(tipo_produto)

            if not Model or not nome:
                return JsonResponse({'success': False, 'error': 'Dados inválidos'})

            # Usamos a variável 'preco_decimal' que foi tratada
            if tipo_produto == 'tamanho':
                novo_produto = Model.objects.create(loja=loja, nome=nome, preco_base=preco_decimal)
            elif tipo_produto == 'adicional':
                novo_produto = Model.objects.create(loja=loja, nome=nome, preco=preco_decimal)
            elif tipo_produto == 'sabor':
                novo_produto = Model.objects.create(loja=loja, nome=nome)

            return JsonResponse({
                'success': True,
                'produto': serialize_produto(novo_produto, tipo_produto)
            })

        except (Decimal.InvalidOperation, ValueError):
             # Captura erros específicos de conversão se o usuário digitar algo como "abc"
            return JsonResponse({'success': False, 'error': 'O valor do preço inserido é inválido.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método inválido'})

@csrf_exempt
def editar_produto(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            tipo_produto = data.get('tipo_produto')
            produto_id = data.get('produto_id')
            nome = data.get('nome')
            preco = data.get('preco')

            model_map = {'tamanho': Tamanho, 'sabor': Sabor, 'adicional': Adicional}
            Model = model_map.get(tipo_produto)

            if not all([Model, produto_id, nome]):
                return JsonResponse({'success': False, 'error': 'Dados inválidos'})

            # Busca o produto existente no banco
            produto = Model.objects.get(id=produto_id)

            # Atualiza os campos
            produto.nome = nome
            if tipo_produto in ['tamanho', 'adicional']:
                # Reutilizamos a mesma lógica de validação de preço
                if not preco:
                    preco_decimal = Decimal('0.00')
                else:
                    preco_formatado = str(preco).replace(',', '.').strip()
                    preco_decimal = Decimal(preco_formatado)

                if tipo_produto == 'tamanho':
                    produto.preco_base = preco_decimal
                else:
                    produto.preco = preco_decimal

            produto.save() # Salva as alterações

            return JsonResponse({
                'success': True,
                'produto': serialize_produto(produto, tipo_produto)
            })

        except (Model.DoesNotExist):
            return JsonResponse({'success': False, 'error': 'Produto não encontrado'})
        except (Decimal.InvalidOperation, ValueError):
            return JsonResponse({'success': False, 'error': 'O valor do preço inserido é inválido.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método inválido'})

@csrf_exempt
def excluir_produto(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            tipo_produto = data.get('tipo_produto')
            produto_id = data.get('produto_id')

            model_map = {'tamanho': Tamanho, 'sabor': Sabor, 'adicional': Adicional}
            Model = model_map.get(tipo_produto)

            if not all([Model, produto_id]):
                return JsonResponse({'success': False, 'error': 'Dados inválidos'})

            # Busca o produto existente e o deleta
            produto = Model.objects.get(id=produto_id)
            produto.delete()

            return JsonResponse({'success': True, 'message': 'Produto excluído com sucesso!'})

        except Model.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Produto não encontrado'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método inválido'})

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

@csrf_exempt
def atualizar_status_pedido(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            pedido_id = data.get('pedido_id')
            novo_status = data.get('novo_status')

            # Valida se os status permitidos estão sendo enviados
            status_validos = ['recebido', 'em_preparo', 'pronto', 'entregue', 'cancelado']
            if novo_status not in status_validos:
                return JsonResponse({'success': False, 'error': 'Status inválido'})

            # Busca o pedido, atualiza o status e salva
            pedido = Pedido.objects.get(id=pedido_id)
            pedido.status = novo_status
            pedido.save()

            return JsonResponse({'success': True, 'message': f'Status do pedido {pedido_id} atualizado para {novo_status}'})

        except Pedido.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Pedido não encontrado'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método inválido'})


def detalhes_pedido(request, pedido_id):
    try:
        # 1. Busca o pedido principal
        pedido = Pedido.objects.get(id=pedido_id)

        # 2. Prepara uma lista para guardar os itens formatados
        itens_formatados = []

        # 3. Itera sobre cada "ItemPedido" (cada 'caixa') relacionado a este pedido
        #    Usamos 'pedido.itens.all()' porque definimos related_name='itens' no model ItemPedido
        for item_pedido in pedido.itens.all():
            # Pega todos os produtos (ingredientes) dentro deste item
            produtos_do_item = list(item_pedido.produtos.values('nome', 'preco', 'categoria__nome'))

            # Cria um dicionário para este item montado
            item_data = {
                'produtos': produtos_do_item
            }
            itens_formatados.append(item_data)

        # 4. Junta os campos de endereço em um único texto para exibição
        endereco_completo = f"{pedido.endereco_rua}, {pedido.endereco_numero} - {pedido.endereco_bairro}"
        if pedido.endereco_referencia:
            endereco_completo += f" ({pedido.endereco_referencia})"

        # 5. Monta o dicionário final com todos os dados corretos
        data = {
            'id': pedido.id,
            'hora': pedido.data_hora_pedido.strftime('%H:%M'),
            'cliente_nome': pedido.nome_cliente,
            'cliente_telefone': pedido.telefone_cliente,
            'cliente_endereco': endereco_completo,
            'itens': itens_formatados, # A nova lista de itens separados
            'observacoes': pedido.observacoes,
            'total': f'{pedido.total:.2f}'.replace('.',','),
            'pagamento': pedido.forma_pagamento.nome if pedido.forma_pagamento else 'Não informado',
        }

        return JsonResponse({'success': True, 'pedido': data})
    except Pedido.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Pedido não encontrado'})

@csrf_exempt
def atribuir_entregador(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            pedido_id = data.get('pedido_id')
            entregador_id = data.get('entregador_id')

            pedido = Pedido.objects.get(id=pedido_id)

            # Se o ID do entregador for nulo ou vazio, desatribui
            if not entregador_id:
                pedido.entregador = None
            else:
                entregador = Entregador.objects.get(id=entregador_id)
                pedido.entregador = entregador

            pedido.save()
            return JsonResponse({'success': True, 'message': 'Entregador atribuído com sucesso!'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método inválido'})

@csrf_exempt
def reordenar_categorias(request):
    if request.method == 'POST':
        try:
            # Recebe a lista de IDs na nova ordem enviada pelo JavaScript
            data = json.loads(request.body)
            ordem_ids = data.get('ordem_ids', [])

            # Itera sobre a lista recebida
            for index, categoria_id in enumerate(ordem_ids):
                # Atualiza o campo 'ordem' de cada categoria com sua nova posição (índice)
                Categoria.objects.filter(id=categoria_id).update(ordem=index)

            return JsonResponse({'success': True, 'message': 'Ordem das categorias atualizada com sucesso!'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método inválido'})