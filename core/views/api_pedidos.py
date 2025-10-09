import json
from decimal import Decimal
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Sum, Count
from django.db.models.functions import Coalesce
from collections import Counter
from core.models import Loja, Pedido, Produto, FormaPagamento, Entregador, ItemPedido


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