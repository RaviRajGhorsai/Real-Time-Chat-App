from channels.generic.websocket import WebsocketConsumer
from django.shortcuts import get_object_or_404
from .models import Group, GroupMessage, User, Profile
from django.template.loader import render_to_string
from asgiref.sync import async_to_sync
import json
from cryptography.fernet import Fernet
import os
import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(
        DEBUG=(bool, False)
)

environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

f = Fernet(env('ENCRYPT_KEY'))

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        self.group_name = self.scope['url_route']['kwargs']['chat_room_name']
        self.chat_room = get_object_or_404(Group, name=self.group_name)
        
        # converts asynchronous function to synchronous, so that all user can 
        # receive message at once in real time
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )
        
        if self.user not in self.chat_room.online_users.all():
            self.chat_room.online_users.add(self.user)
            self.update_online_count()
        
        self.accept()
    
    # disconnect method is called when the user disconnects from the websocket
    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, self.channel_name)
        
        if self.user in self.chat_room.online_users.all():
            self.chat_room.online_users.remove(self.user)
            self.update_online_count()
    
    def receive(self, text_data):
        
        test_json_data = json.loads(text_data)
        message = test_json_data.get('message', '').strip()
        if not message:
            print("No message received")
            return
        print(message)
        plain_text = message
        message = f.encrypt(plain_text.encode()).decode()
        try:
            group_message = GroupMessage.objects.create(
                group=self.chat_room,
                user=self.user,
                message=message
            )
            group_message.save()
        except Exception as e:
            print(f"Error saving message: {e}")
            return
        
        event = {
            'type': 'message_handler',
            'message': message,
            'user': self.user.username,
            'group_name': self.group_name,
            'message_id': group_message.id,
        }
        
        # Send the event/message to the group
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,event
        )
    
    def message_handler(self, event):
        
        message_id = event['message_id']
        group_message = get_object_or_404(GroupMessage, id=message_id)
        sender = group_message.user
        
        sender_profile, _ = Profile.objects.get_or_create(user=sender)
        context ={
            'message': group_message,
            'user': self.user,
            'sender_profile': sender_profile
        }
        html = render_to_string('chat/partials/chat_message_p.html', context=context)
        
        self.send(text_data=html)
        
    def update_online_count(self):
        online_count = self.chat_room.online_users.count() -1
        event = {
            'type': 'online_count_handler',
            'online_count': online_count,
        }
        
        async_to_sync(self.channel_layer.group_send)(
            self.group_name, event
        )
    
    def online_count_handler(self, event):
        online_count = event['online_count']
      
        html = render_to_string('chat/partials/online_count.html', {'online_count': online_count})
        self.send(text_data=html)