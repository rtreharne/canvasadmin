from django.db import models

from core.models import Assignment, Submission, Course

class CourseMarker(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    grader = models.CharField(max_length=128)
    graded_count = models.IntegerField()

    def __str__(self):
        return self.course.course_code
