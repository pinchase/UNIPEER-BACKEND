import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import CollaborationRoom, Message
from .serializers import MessageSerializer


class RoomChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = int(self.scope['url_route']['kwargs']['room_id'])
        self.room_group_name = f'room_{self.room_id}'
        self.user = self.scope.get('user')

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4401)
            return

        if not await self.user_is_room_member():
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'room_id': self.room_id,
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': 'Invalid JSON payload',
            }))
            return

        action = payload.get('action')
        if action != 'send_message':
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': 'Unsupported action',
            }))
            return

        content = (payload.get('content') or '').strip()
        if not content:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': 'Message content is required',
            }))
            return

        message = await self.create_message(content)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'message': message,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_created',
            'message': event['message'],
        }))

    @database_sync_to_async
    def user_is_room_member(self):
        return CollaborationRoom.objects.filter(id=self.room_id, members__user=self.user).exists()

    @database_sync_to_async
    def create_message(self, content):
        room = CollaborationRoom.objects.get(id=self.room_id)
        sender = self.user.profile
        message = Message.objects.create(room=room, sender=sender, content=content)
        serialized = Message.objects.select_related('sender__user', 'room').get(id=message.id)
        return MessageSerializer(serialized).data
