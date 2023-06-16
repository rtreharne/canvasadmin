from django.db import models
from core.models import Course

"""
Create an Enrollment model that will store the following information:
    - student
    - course
    - page_views
    - participations
    - average_assignment_score
"""

class Enrollment(models.Model):
    canvas_id = models.IntegerField()
    canvas_course_id = models.IntegerField()
    canvas_user_id = models.IntegerField()
    sis_user_id = models.CharField(max_length=255)
    login_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    page_views = models.IntegerField(blank=True, null=True)
    participations = models.IntegerField(blank=True, null=True)
    average_assignment_score = models.FloatField(blank=True, null=True)

    def __str__(self):
        return self.name
