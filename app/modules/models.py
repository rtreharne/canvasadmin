from django.db import models
from core.models import Course

class Module(models.Model):
    name = models.CharField(max_length=256, verbose_name="Module Title")
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    module_id = models.IntegerField()
    unlock_at = models.DateTimeField(null=True, blank=True)
    published = models.BooleanField(default=False)

    class Meta:
        unique_together = ('name', 'course')

    def __str__(self):
        return self.name
