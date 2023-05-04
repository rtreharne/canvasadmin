from django.db import models
from core.models import Course, Assignment, Student, Staff

# Create your models here.

# Thinking about model construction

class Category(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    canvas_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name
    
class Group(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    canvas_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name
