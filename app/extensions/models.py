from django.db import models
from core.models import Student, Course, Assignment
from accounts.models import UserProfile
from core.models import Assignment

class Extension(models.Model):

    EXTENSION_CHOICES = (
        ('EXTENSION', 'Extension'),
        ('ELP', 'Exemption from late penalty (ELP)')
    )

    unique_id = models.IntegerField(null=True, blank=True, editable=False)
    student = models.ForeignKey(Student, verbose_name="Student", on_delete=models.PROTECT, null=True, blank=True)
    extension_type = models.CharField(max_length=128, choices=EXTENSION_CHOICES, default='EXTENSION')
    date_of_application = models.DateTimeField(auto_now_add=True)
    course = models.ForeignKey(Course, on_delete=models.PROTECT, null=True, blank=True, editable=False)
    assignment = models.ForeignKey(Assignment, on_delete=models.PROTECT, verbose_name="Assignment")
    approved = models.BooleanField(default=False, editable=False, verbose_name="Approved")
    approved_by = models.ForeignKey(UserProfile, verbose_name="Approver", null=True, blank=True, on_delete=models.PROTECT, editable=False)
    approved_on = models.DateTimeField(null=True, blank=True, editable=False)
    extension_deadline = models.DateTimeField(null=True, blank=True)
    original_deadline = models.DateTimeField(null=True, blank=True, editable=False)
    apply_to_subcomponents = models.BooleanField(default=False)
    reason = models.TextField(null=True, blank=True)
    files = models.FileField(upload_to='extensions/', null=True, blank=True)

    def __str__(self):
        return str(self.student_id)
    
    def save(self, *args, **kwargs):
        course = self.assignment.course
        self.course = course
        if self.apply_to_subcomponents:
            component = ".".join(self.assignment.assignment_name.split(".")[:2])
            print(self.assignment.assignment_name, component)
            assignments = Assignment.objects.filter(assignment_name__contains=component)
            for a in assignments:
                new_extension = self
                new_extension.pk = None
                new_extension.assignment = a
                new_extension.apply_to_subcomponents = False
                new_extension.save()
        super(Extension, self).save(*args, **kwargs)


