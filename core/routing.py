# core/routing.py

from django.urls import re_path
from . import consumers # Importa nosso novo arquivo consumers.py

websocket_urlpatterns = [
    # Esta linha diz ao Channels:
    # "Quando uma conexão WebSocket chegar no endereço 'ws/painel/ID_DA_LOJA/',
    # ela deve ser gerenciada pelo PedidoConsumer."
    re_path(r'ws/painel/(?P<loja_id>\w+)/$', consumers.PedidoConsumer.as_asgi()),
]