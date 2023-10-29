import json
from pprint import pprint

from django.utils import timezone
from faker import Faker


# Async
from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        fake = Faker()
        self.author_name = fake.name()
        author_id = self.channel_name.split("!")[1][:7]

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # # Send greetings
        message = f"{'-'*5} {self.author_name} присоединяется к чату! [uid:{author_id}] {'-'*5}"
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat.message", "message": message}
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        timestamp = timezone.now().strftime("%H:%M")

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name, {
                "type": "chat.message",
                "message": f"[{timestamp}] {self.author_name}: {message}",
                # "message": message,
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]

        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message}))


# Sync
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync


class ChatConsumerSync(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        pprint(self.scope)
        self.room_group_name = f"chat_{self.room_name}"

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        pprint(f'{self.room_group_name}')
        pprint(f'{self.channel_name=}')

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        pprint(text_data)
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {"type": "chat.message", "message": message}
        )

    # Receive message from room group
    def chat_message(self, event):
        message = event["message"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": f"{self.channel_name}: {message}"}))
        # self.send(text_data=json.dumps({"message": message}))


class ChatConsumerSimple(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        self.send(text_data=json.dumps({"message": message}))
