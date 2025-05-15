from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup, name='signup'),
    path('otp-verify/', views.otp_verify, name='otp_verify'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    # path('create-group/', views.create_group_view, name='create_group'),
    # path('join-group/', views.join_group_view, name='join_group'),
    path('chat/', views.chat_view, name='joinChat'),
    path('profile/<str:username>', views.profile_view, name='profile'),
    path('chat/<username>', views.get_or_create_chat, name='start-chat'),
    path('chat/room/<chatroom_name>', views.chat_view, name="chatroom"),
    path('upload-img/', views.upload_img, name='profile-img'),
]