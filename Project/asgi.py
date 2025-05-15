"""
ASGI config for Project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django

django.setup()

from django.core.asgi import get_asgi_application 
from channels.routing import ProtocolTypeRouter, URLRouter, get_default_application
from channels.auth import AuthMiddlewareStack
from app import routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings')
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})