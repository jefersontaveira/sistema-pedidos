# core/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class PedidoConsumer(AsyncWebsocketConsumer):
    # Chamado quando o frontend tenta se conectar a este consumer
    async def connect(self):
        # Pega o ID da loja a partir da URL
        self.loja_id = self.scope['url_route']['kwargs']['loja_id']
        self.room_group_name = f'pedidos_{self.loja_id}'

        print(f"--- CONSUMER: Conectando e entrando no grupo '{self.room_group_name}' ---")

        # Adiciona o canal (a conexão do usuário) ao grupo da loja
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Aceita a conexão WebSocket
        await self.accept()

    # Chamado quando a conexão é fechada
    async def disconnect(self, close_code):
        # Remove o canal do grupo da loja
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Esta função é chamada quando recebemos uma mensagem do grupo do canal
    # O nome dela (novo_pedido_message) deve corresponder à chave 'type' da mensagem que enviaremos
    async def novo_pedido_message(self, event):
        print(f"--- CONSUMER: Mensagem recebida no grupo '{self.room_group_name}' ---")

        message = event['message']

        # Envia a mensagem para o WebSocket (para o navegador do atendente)
        await self.send(text_data=json.dumps({
            'type': 'novo_pedido',
            'message': message
        }))