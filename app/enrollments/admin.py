from django.contrib import admin

# Register your models here.

from .models import Enrollment
from core.admin_actions import export_as_csv_action

class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("name", "course", "canvas_course_id", "page_views", "participations", "average_assignment_score")

    list_filter = ("name","course",)

    actions = [export_as_csv_action(),]

admin.site.register(Enrollment, EnrollmentAdmin)
