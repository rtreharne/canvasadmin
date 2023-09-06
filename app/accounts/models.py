from django.db import models
from django.contrib.auth.models import User

class Department(models.Model):
    name = models.CharField(max_length=128)
    CANVAS_API_TOKEN = models.CharField(max_length=128)
    CANVAS_API_URL = models.URLField()
    course_prefixes = models.CharField(max_length=128, null=True, blank=True, help_text="This should be a comma separated list, e.g. PHYS,MATH,CHEM")
    label = models.CharField(max_length=8, null=True, blank=True)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.PROTECT)

    def __str__(self):
        return self.user.username
