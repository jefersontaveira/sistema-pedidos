# core/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # ... (rota admin_geral) ...
    path('api/atualizar-disponibilidade/', views.atualizar_disponibilidade, name='atualizar_disponibilidade'),
    path('api/adicionar-produto/', views.adicionar_produto, name='adicionar_produto'),
    path('api/editar-produto/', views.editar_produto, name='editar_produto'),
    path('api/excluir-produto/', views.excluir_produto, name='excluir_produto'),

    # Rota para adicionar, excluir uma categoria.
    path('api/adicionar-categoria/', views.adicionar_categoria, name='adicionar_categoria'),
    path('api/excluir-categoria/', views.excluir_categoria, name='excluir_categoria'),

    path('api/atualizar-status-pedido/', views.atualizar_status_pedido, name='atualizar_status_pedido'),
    path('api/detalhes-pedido/<int:pedido_id>/', views.detalhes_pedido, name='detalhes_pedido'),

    path('admin-loja/<int:loja_id>/', views.admin_geral, name='admin_geral'),

    # Para popular a area de entregar do card
    path('api/atribuir-entregador/', views.atribuir_entregador, name='atribuir_entregador'),

    # Api do Dashboard
    path('api/dashboard-data/<int:loja_id>/', views.dashboard_data, name='dashboard_data'),

    # URLs do Painel do Lojista
    path('painel/<int:loja_id>/', views.painel_loja, name='painel_loja'),

    # URLs da API (usadas pelo JavaScript)
    path('loja/finalizar-pedido/', views.finalizar_pedido, name='finalizar_pedido'),

    # URLs da Página do Cliente (deve vir por último por ser mais genérica)
    path('loja/<uuid:slug_da_loja>/', views.pagina_loja, name='pagina_loja'),

    # URL para mudar a ordem das categorias
    path('api/reordenar-categorias/', views.reordenar_categorias, name='reordenar_categorias'),
]