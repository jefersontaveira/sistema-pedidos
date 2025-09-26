# core/admin.py

from django.contrib import admin
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


# Classe de customização para a exibição da Loja
class LojaAdmin(admin.ModelAdmin):
    # Mostra estes campos na lista de todas as lojas
    list_display = ('nome', 'slug', 'ativa', 'dia_vencimento_mensalidade')

    # Mostra o campo 'slug' como apenas leitura na página de edição/detalhes
    readonly_fields = ('slug',)

    # Adiciona uma barra de busca
    search_fields = ('nome', 'cnpj', 'nome_proprietario')

    # Adiciona filtros na lateral
    list_filter = ('ativa',)

class AcessoLojaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'loja', 'funcao')
    list_filter = ('loja', 'funcao')

class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'loja', 'ordem')
    list_filter = ('loja',)

class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'preco', 'disponivel')
    list_filter = ('categoria', 'disponivel', 'categoria__loja')
    search_fields = ('nome', 'descricao')

# Este é um "Inline": permite editar os Itens DENTRO da página do Pedido
class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 1 # Quantos campos de item extra mostrar
    filter_horizontal = ('produtos',)

class PedidoAdmin(admin.ModelAdmin):
    list_display = ('nome_cliente', 'loja', 'total', 'status', 'data_hora_pedido')
    list_filter = ('status', 'loja', 'data_hora_pedido')
    search_fields = ('nome_cliente', 'id')
    inlines = [ItemPedidoInline] # Adiciona o inline de ItemPedido




# Agora, registramos a Loja usando esta classe de customização
admin.site.register(Loja, LojaAdmin)

# Registra os outros models da forma padrão
admin.site.register(AcessoLoja, AcessoLojaAdmin)
admin.site.register(Categoria, CategoriaAdmin)
admin.site.register(Produto, ProdutoAdmin)

admin.site.register(Pedido, PedidoAdmin)

admin.site.register(FormaPagamento)
admin.site.register(Entregador)
admin.site.register(Cupom)
admin.site.register(ItemPedido)


