from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Favorite

@receiver(post_save, sender=User)
def merge_favorites(sender, instance, created, **kwargs):
    """
    Ro'yxatdan o'tgan foydalanuvchining sessiyadagi sevimlilarini
    foydalanuvchi hisobiga o'tkazadi.
    """
    if not created:  # Faqat yangi foydalanuvchi yaratilganda ishlaydi
        return

    session_key = getattr(instance, 'session_key', None)
    if session_key:
        session_favorites = Favorite.objects.filter(session_key=session_key)
        for favorite in session_favorites:
            favorite.user = instance
            favorite.session_key = None
            favorite.save()
