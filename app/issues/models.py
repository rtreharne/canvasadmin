from django.db import models

# Create your models here.

class Status(models.Model):
    title=models.CharField(max_length=128)

    def __str__(self) -> str:
        return self.title

class Issue(models.Model):
    choices = [
        ('low','Low'),
        ('medium','Medium')
        ('high','High')

    ]
    statuses = []

    title = models.CharField(max_length=128)
    description = models.TextField(null=True,blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    priority = models.CharField(max_length=128,choices=choices)
    status = models.CharField(max_length=128,choices=statuses)

