from django.apps import AppConfig

class JobinfoApplicationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jobinfo_application'

    def ready(self):
        import jobinfo_application.signals