from django.shortcuts import render
from app.models import User

# Create your views here.

def search_users(request):
    
    search_friend = request.GET.get("search")
    if search_friend:
        users = User.objects.filter(username__icontains = search_friend)
    else:
        users = User.objects.all().exclude(username="sudo")
    return render(request, 'newsfeed/sidebar.html', {'friends': users})