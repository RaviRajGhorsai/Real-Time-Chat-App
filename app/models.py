from django.db import models
from django.contrib.auth.models import AbstractUser
import shortuuid
import uuid
from cloudinary.models import CloudinaryField
# Create your models here.

class User(AbstractUser):
    # Add any additional fields you want to the user model here
    email = models.EmailField(unique=True)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    # image = models.ImageField(upload_to='uploads/', blank=True, null=True)
    image = CloudinaryField(blank=True, null=True)
    
    def __str__(self):
        return self.user.username
    
class Group(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, default=shortuuid.uuid, unique=True)
    online_users = models.ManyToManyField(User, related_name='online_count', blank=True)
    members = models.ManyToManyField(User, related_name='members', blank=True)
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class GroupMessage(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    message = models.CharField(max_length=300, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.message}"