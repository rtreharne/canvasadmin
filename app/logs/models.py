from django.db import models
from core.models import Assignment
from accounts.models import Department

class AssignmentLog(models.Model):
    assignment = models.CharField(max_length=500, verbose_name="Assignment")
    course = models.CharField(max_length=128, verbose_name="Course")
    request = models.CharField(max_length=128, choices=(
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
        ("CREATE", "Create")
    ))
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Timestamp")
    field = models.CharField(max_length=128, null=True, blank=True)
    from_value = models.CharField(max_length=500, null=True)
    to_value = models.CharField(max_length=500, null=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, null=True, blank=True)
    


    def __str__(self):
        return self.assignment

class SubmissionLog(models.Model):
    student = models.CharField(max_length=128, verbose_name="Student")
    submission = models.CharField(max_length=500, verbose_name="Assignment")
    course = models.CharField(max_length=128, verbose_name="Course")
    request = models.CharField(max_length=128, choices=(
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
        ("CREATE", "Create")
    ))
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Timestamp")
    field = models.CharField(max_length=128, null=True, blank=True)
    from_value = models.CharField(max_length=128, null=True)
    to_value = models.CharField(max_length=128, null=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, null=True, blank=True)


    def __str__(self):
        return self.student