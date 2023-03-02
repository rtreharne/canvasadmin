from django.contrib import admin
from .tasks import submission_recon

from .models import CourseMarker

class CourseMarkerAdmin(admin.ModelAdmin):
    list_display = ("course", "grader", "graded_count")

    
admin.site.register(CourseMarker, CourseMarkerAdmin)
