from django.contrib import admin
from .models import JobApplication, Document, UserProfile, JobType

admin.site.register(JobApplication)
admin.site.register(Document)
admin.site.register(UserProfile)
admin.site.register(JobType)