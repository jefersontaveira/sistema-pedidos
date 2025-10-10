
import json
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Max

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

@csrf_exempt
def adicionar_categoria(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            loja_id = data.get('loja_id')
            nome_categoria = data.get('nome')

            loja = Loja.objects.get(id=loja_id)

            if not nome_categoria:
                return JsonResponse({'success': False, 'error': 'O nome da categoria é obrigatório.'})

            # --- INÍCIO DA NOVA LÓGICA DE ORDEM AUTOMÁTICA ---
            # 1. Busca a maior 'ordem' que já existe para esta loja.
            ultima_ordem = Categoria.objects.filter(loja=loja).aggregate(Max('ordem'))['ordem__max']

            # 2. Define a nova ordem. Se não houver nenhuma categoria, começa com 0. Senão, adiciona 1.
            nova_ordem = 0 if ultima_ordem is None else ultima_ordem + 1
            # --- FIM DA NOVA LÓGICA ---

            # Cria a nova categoria com a ordem calculada
            nova_categoria = Categoria.objects.create(
                loja=loja,
                nome=nome_categoria,
                ordem=nova_ordem # Usa a nova ordem
            )

            return JsonResponse({
                'success': True,
                'categoria': {
                    'id': nova_categoria.id,
                    'nome': nova_categoria.nome,
                    'ordem': nova_categoria.ordem
                }
            })

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

@csrf_exempt
def excluir_categoria(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            categoria_id = data.get('categoria_id')

            # Encontra a categoria no banco de dados e a deleta.
            # Graças ao 'on_delete=models.CASCADE' no model Produto,
            # todos os produtos desta categoria serão apagados junto.
            categoria = Categoria.objects.get(id=categoria_id)
            categoria.delete()

            return JsonResponse({'success': True, 'message': 'Categoria e seus produtos foram excluídos.'})

        except Categoria.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Categoria não encontrada.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método inválido'})

@csrf_exempt
def editar_categoria(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            categoria_id = data.get('categoria_id')

            categoria = Categoria.objects.get(id=categoria_id)

            # Atualiza os campos com os dados recebidos
            categoria.nome = data.get('nome', categoria.nome)
            categoria.save()

            return JsonResponse({
                'success': True,
                'categoria': {
                    'id': categoria.id,
                    'nome': categoria.nome,
                    'ordem': categoria.ordem
                }
            })
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
            produto_id = data.get('produto_id')

            # Validação para garantir que um ID foi enviado
            if not produto_id:
                return JsonResponse({'success': False, 'error': 'ID do produto não foi fornecido.'})

            # 1. Encontra o produto no banco de dados usando o ID.
            #    Usamos 'Produto' diretamente, pois sabemos qual tabela procurar.
            produto = Produto.objects.get(id=produto_id)

            # 2. Deleta o objeto do banco de dados.
            produto.delete()

            # 3. Retorna uma resposta de sucesso para o JavaScript.
            return JsonResponse({'success': True, 'message': 'Produto excluído com sucesso!'})

        except Produto.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Produto não encontrado.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método inválido'})

def serialize_produto(produto):
    categoria = produto.categoria
    data = {
        'id': produto.id,
        'nome': produto.nome,
        'descricao': produto.descricao or '',
        'disponivel': produto.disponivel,
        'categoria_id': categoria.id,
        'categoria_nome': categoria.nome,
        'preco': f'{produto.preco:.2f}'.replace('.', ','),
        'foto_url': produto.foto.url if produto.foto else None # Adiciona a URL da foto
    }
    return data


@csrf_exempt
def adicionar_produto(request):
    if request.method == 'POST':
        try:
            # Para FormData, os dados de texto vêm em request.POST
            # e os arquivos vêm em request.FILES

            loja = Loja.objects.get(id=request.POST.get('loja_id'))
            categoria = Categoria.objects.get(id=request.POST.get('categoria'))
            nome = request.POST.get('nome')
            descricao = request.POST.get('descricao')
            preco_str = request.POST.get('preco', '0')
            foto = request.FILES.get('foto')  # Pega o arquivo de imagem

            if not nome or not preco_str:
                return JsonResponse({'success': False, 'error': 'Nome e preço são obrigatórios.'})

            preco_decimal = Decimal(str(preco_str).replace(',', '.'))

            # Cria o novo produto, incluindo a foto se ela foi enviada
            novo_produto = Produto.objects.create(
                loja=loja,
                categoria=categoria,
                nome=nome,
                descricao=descricao,
                preco=preco_decimal,
                foto=foto
            )

            # A função serialize_produto precisa ser ajustada para retornar a URL da foto
            return JsonResponse({'success': True, 'produto': serialize_produto(novo_produto)})

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
def atualizar_disponibilidade(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            produto = Produto.objects.get(id=data.get('produto_id'))
            produto.disponivel = data.get('disponivel')
            produto.save()
            return JsonResponse({'success': True, 'message': 'Disponibilidade atualizada com sucesso!'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método inválido'})