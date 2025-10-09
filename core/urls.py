# core/urls.py

from django.urls import path
from .views import paginas, api_cardapio, api_pedidos, api_dashboard

urlpatterns = [
    # --- Rotas de Páginas Visíveis para o Usuário ---
    path('admin-loja/<int:loja_id>/', paginas.admin_geral, name='admin_geral'),
    path('loja/<int:loja_id>/', paginas.pagina_loja, name='pagina_loja'),

    # --- Rotas de API do Cardápio (usadas pelo admin_panel.js) ---
    path('api/adicionar-categoria/', api_cardapio.adicionar_categoria, name='adicionar_categoria'),
    path('api/editar-categoria/', api_cardapio.editar_categoria, name='editar_categoria'),
    path('api/excluir-categoria/', api_cardapio.excluir_categoria, name='excluir_categoria'),
    path('api/reordenar-categorias/', api_cardapio.reordenar_categorias, name='reordenar_categorias'),
    path('api/adicionar-produto/', api_cardapio.adicionar_produto, name='adicionar_produto'),
    path('api/editar-produto/', api_cardapio.editar_produto, name='editar_produto'),
    path('api/excluir-produto/', api_cardapio.excluir_produto, name='excluir_produto'),
    path('api/atualizar-disponibilidade/', api_cardapio.atualizar_disponibilidade, name='atualizar_disponibilidade'),

    # --- Rotas de API de Pedidos (usadas pelo main.js e admin_panel.js) ---
    path('loja/finalizar-pedido/', api_pedidos.finalizar_pedido, name='finalizar_pedido'),
    path('api/atualizar-status-pedido/', api_pedidos.atualizar_status_pedido, name='atualizar_status_pedido'),
    path('api/detalhes-pedido/<int:pedido_id>/', api_pedidos.detalhes_pedido, name='detalhes_pedido'),
    path('api/atribuir-entregador/', api_pedidos.atribuir_entregador, name='atribuir_entregador'),

    # --- Rotas de API do Dashboard (usadas pelo admin_panel.js) ---
    path('api/dashboard-data/<int:loja_id>/', api_dashboard.dashboard_data, name='dashboard_data'),
]