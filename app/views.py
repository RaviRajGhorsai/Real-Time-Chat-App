from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.contrib.auth import get_user_model, authenticate, logout, login
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib import messages
from datetime import datetime, timedelta
import hashlib
import secrets
from utils import send_register_mail, send_otp_mail, verify_mail
from .models import Group, GroupMessage, Profile
from .forms import chatMessageForm
from django.db.models import Count, Q
from django.db import IntegrityError
from cryptography.fernet import Fernet
import os
import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(
    DEBUG=(bool, False)
)

User = get_user_model()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

f = Fernet(env('ENCRYPT_KEY'))

def home_view(request):
    return render(request, 'dashboard.html')

@csrf_exempt
def signup(request):
    if request.method == 'POST':
        # Handle the signup logic 
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        email = request.POST.get('email')
       
        if password1 != password2:
            print("passwords do not match")
            return render(request, 'signup.html', {'error': 'passwords do not match'})
        
        if not username or not email or not password1:
            print("all fields are required")
            return render(request, 'signup.html', {'error': 'all fields are required'})
        
        try:
            validate_email(email)
        except ValidationError:
            print("Invalid email address")
            return render(request, 'signup.html', {'error': 'Invalid email address'})
        
        if User.objects.filter(username=username).exists():
            return HttpResponse("Username already exists!")
        
        if User.objects.filter(email=email).exists():
            return HttpResponse("Email already exists!")
        
        email_verification = verify_mail(email)
        if email_verification == True:
            user = User.objects.create_user(username=username, password=password1, email=email)
            group, created = Group.objects.get_or_create(name="Public")
            group.members.add(user)
            
            send_register_mail(email, username)
            return redirect('app:login')  # Redirect to the login page after signup
        else:
            print("Email is not deliverable")
            return render(request, 'signup.html', {'error': 'Email does not exist'})
                    
    return render(request, 'signup.html')

def login_view(request):
    if request.method == 'POST':
        # Handle the login logic 
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            request.session['otp_verified'] = True
            otp = ''.join(str(secrets.randbelow(10)) for _ in range(6))
            request.session['otp'] = hashlib.sha256(otp.encode()).hexdigest()
            request.session['user_id'] = user.id
            request.session['otp-created-at'] = datetime.now().isoformat()
            
            try:
                send_otp_mail(user.email, otp)
            except Exception as e:
                print(f"Error sending email: {e}")
                return render(request, 'login.html', {'error': 'Failed to send OTP email'})
            # Redirect to the OTP verification page 
            return redirect('app:dashboard')  
        else:
            print("invalid credentials")
            return render(request, 'login.html', {'error': 'Invalid username or password'})
        
    return render(request, 'login.html')

def otp_verify(request):
    if request.method == 'POST':
        # Handle the OTP verification logic 
        entered_otp = ''.join([request.POST.get(str(i), '') for i in range(6)])
        
        actual_otp = request.session.get('otp')
        entered_otp_hash = hashlib.sha256(entered_otp.encode()).hexdigest()
        
        user_id = request.session.get('user_id')
        
        if not actual_otp or not user_id:
            return render(request, 'otp.html', {'error': 'Session expired. Please login again.'})
        
        # Check if the OTP is expired
        otp_time = datetime.fromisoformat(request.session.get('otp-created-at'))
        if entered_otp_hash == str(actual_otp):
            if datetime.now() - otp_time > timedelta(minutes=5):
                
                return render(request, 'otp.html', {'error': 'OTP expired. Please request a new one.'})
            else:
                user = User.objects.get(id=user_id)
                request.session.pop('otp', None)
                request.session.pop('user_id', None)
                request.session.pop('otp-created-at', None)
                request.session.delete()
                
                
                
                login(request, user)
                request.session['otp_verified'] = True
                return redirect('app:dashboard')
        else:
            return render(request, 'otp.html', {'error': 'Invalid OTP. Please try again.'})
    return render(request, 'otp.html')

@login_required
def dashboard(request):
    if request.user.is_authenticated == True:
        if request.session.get('otp_verified') == True:
            print("hello from dashboard")
            
            return render(request, 'newsfeed/home.html', {'user': request.user})
        else:
            print("User is not authenticated")
            return redirect('app:login')  # Redirect to the login page if not authenticated
    
@login_required   
def profile_view(request, username):
    if request.user.is_authenticated:
        if request.session.get('otp_verified') == True:
            user = User.objects.get(username=username)
            profile = Profile.objects.filter(user=user).first()
            context = {
                'username': username,
                'profile': profile
            }
            return render(request, 'chat/profile.html', context)
            
def upload_img(request):
    if request.method =="POST":
        img = request.FILES.get("image")
        if img:
            profile, created = Profile.objects.get_or_create(user=request.user)
            profile.image = img
            profile.save()
            print("upload success")
            return redirect('app:dashboard')
        else:
            print("upload img unsuccess")
    return render(request, 'chat/upload.html')

@login_required
def chat_view(request, chatroom_name="Public"):
    if request.user.is_authenticated == True:
        if request.session.get('otp_verified') == True:
            
            chat_group = get_object_or_404(Group, name=chatroom_name)
            chat_messages = chat_group.messages.order_by('-created')[:30][::-1]
            form = chatMessageForm()
        
            other_user = chat_group.members.exclude(id=request.user.id)
            profile = Profile.objects.filter(user__in=other_user)
            
            
            if request.htmx:
                form = chatMessageForm(request.POST)
                if form.is_valid():
                    
                    message = form.save(commit=False)
                    message.user = request.user
                    message.group = chat_group
                    
                    message.save()
                    sender_profile = Profile.objects.filter(user=message.user).first()
                    context = {
                        'message': message,
                        'user': request.user,
                        'other_user': other_user, 
                        'sender_profile': sender_profile, 
                    }
                    
                    return render(request, 'chat/partials/chat_message_p.html', context)
            chat_groups = Group.objects.filter(members=request.user)
            context = {
                'chat_group': chat_group,
                'chat_messages': chat_messages,
                'chat_room_name': chatroom_name,
                'form': form,
                'other_user': other_user,
                'chat_groups_all': chat_groups,
                'profile': profile,  
            }
            return render(request, 'chat/chat.html', context)
        else:
            return redirect('app:login')

def get_or_create_chat(request, username):
    if request.user.username == username:
        redirect('app:dashboard')
    else:
        other_user = User.objects.get(username=username)
        user_ids = sorted([request.user.id, other_user.id])
        room_name = f"private_{user_ids[0]}_{user_ids[1]}"
        
        chatroom = Group.objects.filter(name=room_name, is_private=True).first()
        
        if not chatroom:
            try:
                chatroom = Group.objects.create(name=room_name, is_private=True)
                chatroom.members.add(request.user, other_user)
            except IntegrityError:
                chatroom = Group.objects.get(name=room_name)
                chatroom.members.add(request.user, other_user)
        return redirect('app:chatroom', chatroom.name)

@login_required
def logout_view(request):
    if request.user.is_authenticated:
        
        logout(request)
        request.session.delete()
        return redirect('app:login')  
    return redirect('app:login')  



#@login_required
# def create_group_view(request):
#     if request.user.is_authenticated == True:
#         if request.session.get('otp_verified') == True:
#             if request.method == 'POST':
#                 # Handle the group creation logic 
#                 group_name = request.POST.get('group_name', '').strip()
#                 group_key = request.POST.get('group_key', '').strip()
                
#                 if not group_name or not group_key:
#                     print("All fields are required")
#                     return render(request, 'chat/create_group.html', {'error': 'All fields are required'})
                
#                 if Group.objects.filter(name=group_name).exists():
#                     print("Group name already exists")
#                     return render(request, 'chat/create_group.html', {'error': 'Group name already exists'})
                
#                 group = Group.objects.create(name=group_name, key=group_key)
#                 group.members.add(request.user)
#                 group.save()
#                 if group:
#                     return redirect('chat')
#                 else:
#                     print("Failed to create group")
#                     return render(request, 'chat/create_group.html', {'error': 'Failed to create group'})
#             return render(request, 'chat/create_group.html')
#         else:
#             return redirect('login')

# @login_required
# def join_group_view(request):
#     if request.user.is_authenticated == True:
#         if request.session.get('otp_verified') == True:
#             if request.method == 'POST':
#                 # Handle the group joining logic 
#                 group_key = request.POST.get('groupKey', '').strip()
#                 group_name = request.POST.get('groupName', '').strip()
                
#                 if not group_key or not group_name:
#                     print("Group key is required")
#                     return render(request, 'chat/join_group.html', {'error': 'Group name and key is required'})
        
#                 try:
#                     group = Group.objects.get(name= group_name, key=group_key)
#                 except Group.DoesNotExist:
#                     print("Group does not exist")
#                     return render(request, 'chat/join_group.html', {'error': 'Group does not exist'})
                
#                 if request.user not in group.members.all():
#                     group.members.add(request.user)
#                     group.save()
#                     messages.success(request, f"You have successfully joined the group {group.name}.")
#                     print(f"You have successfully joined the group {group.name}.")
#                     return redirect('chat')
#                 else:
#                     print("You are already a member of this group")
#                     return redirect('chat')
#             return render(request, 'chat/join_group.html')
#         else:
#             return redirect('login')