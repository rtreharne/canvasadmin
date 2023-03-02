from django.db import models
from core.models import Student, Course, Assignment

class Extension(models.Model):

    EXTENSION_CHOICES = (
        ('EXTENSION', 'Extension'),
        ('ELP', 'Exemption from late penalty (ELP)')
    )

    DAYS_CHOICES = (
        ('7', '7 days'),
        ('14', '14 days')
    )
    student_id = models.IntegerField()
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    extension_type = models.CharField(max_length=128, choices=EXTENSION_CHOICES, default='EXTENSION')
    date_of_application = models.DateTimeField(auto_now_add=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    approved = models.BooleanField(default=False)
    days_approved = models.CharField(max_length=128, choices=DAYS_CHOICES, default='7')
    original_deadline = models.DateTimeField(null=True, blank=True)
    further_extension = models.BooleanField(default=False)

    def __str__(self):
        return self.student.sortable_name


