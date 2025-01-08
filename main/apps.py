from django.apps import AppConfig


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'
class ShopConfig(AppConfig):  # ShopConfig ni ilovangiz nomiga mos ravishda o'zgartiring
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        import main.signals