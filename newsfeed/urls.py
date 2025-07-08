from django.urls import path
from . import views

app_name = 'newsfeed'
urlpatterns = [
    path('friends/', views.search_users, name='sidebar')
]
