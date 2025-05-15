from django.forms import ModelForm
from django import forms
from .models import GroupMessage

class chatMessageForm(ModelForm):
    class Meta:
        model = GroupMessage
        fields = ['message']
        widgets = {
            'message': forms.TextInput(attrs={'type':"text",
            'name':"message", 
            'placeholder':"Type your message...", 
            'class':"flex-1 px-4 py-2 border rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500"}),
        }
    
        