from django.contrib import admin
from accounts.models import User, UserProfile, Department

admin.site.register(UserProfile)
admin.site.register(Department)
