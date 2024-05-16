from django.db import models
from core.models import Student, Course, Assignment
from accounts.models import UserProfile
from core.models import Assignment
import uuid
from django.core.exceptions import ValidationError

class Date(models.Model):
    label = models.CharField(max_length=128)
    start = models.DateField(null=True, blank=True)
    finish = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.label
    
    """
    start and finish date range for Date objects cannot overlap.
    """
    def clean(self):
        if self.start and self.finish:
            if self.start > self.finish:
                raise ValidationError("Start date must be before finish date")
            if Date.objects.filter(start__lte=self.finish, finish__gte=self.start).exclude(pk=self.pk).exists():
                raise ValidationError("Date range overlaps with another date range")
            



class Extension(models.Model):

    """
    Give Extension model class a verbose name of "Record
    """
    class Meta:
        verbose_name = "Record"
        verbose_name_plural = "Records"

    EXTENSION_CHOICES = (
        ('EXTENSION', 'Extension'),
        ('ELP', 'Exemption from late penalty (ELP)')
    )

    unique_id = models.IntegerField(null=True, blank=True, editable=False)
    student = models.ForeignKey(Student, verbose_name="Student", on_delete=models.PROTECT, null=True, blank=True)
    extension_type = models.CharField(max_length=128, choices=EXTENSION_CHOICES, default='ELP')
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
    files = models.FileField(upload_to='extensions/evidence', null=True, blank=True, verbose_name="Evidence upload")
    late_ignore = models.BooleanField(default=False, verbose_name="Less than 5 minutes late?")

    confirm_self_certified = models.BooleanField(default=False, verbose_name="I confirm I understand that if I choose to submit this form without evidence my application will be considered as one of two self-certified ELPs available to me during this academic year.")

    # Create a confirmation id field using uuid
    confirmation_id = models.UUIDField(default=uuid.uuid4, editable=False, null=True, blank=True)
    confirmed = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    status_choices = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected')
    )

    status = models.CharField(max_length=128, choices=status_choices, default='PENDING')
    reject_reason = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    

    






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
        return self


