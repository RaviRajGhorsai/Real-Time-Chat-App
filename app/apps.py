from django.apps import AppConfig
import cloudinary
from django.conf import settings

class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        import app.signals

        cloudinary.config(
            cloud_name = settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
            api_key = settings.CLOUDINARY_STORAGE['API_KEY'],
            api_secret = settings.CLOUDINARY_STORAGE['API_SECRET']
        )
    