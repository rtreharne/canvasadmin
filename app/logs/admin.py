from django.contrib import admin
from django.utils.html import format_html
from core.models import Course, Assignment, Student
from .models import AssignmentLog, SubmissionLog
from accounts.models import UserProfile
from core.admin_actions import export_as_csv_action


class AssignmentLogAdmin(admin.ModelAdmin):
    list_display = (
        "assignment",
        "course",
        "request",
        "timestamp",
        "field",
        "from_value",
        "to_value",
    )

    readonly_fields = ('assignment', 'request', 'from_value', 'to_value', 'field', 'course')

    search_fields = ('course', 'request')

    list_filter = ('assignment', 'course', 'timestamp')

    actions = [export_as_csv_action()]

    def course(self, obj):
        return format_html('<a href="{}" target="_blank">{}</a>'.format(obj.assignment.url, obj.assignment.course))

    def get_queryset(self, request):
        user_profile = UserProfile.objects.get(user=request.user)
        queryset = AssignmentLog.objects.filter(department=user_profile.department)
        return queryset

class SubmissionLogAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "submission",
        "course",
        "request",
        "timestamp",
        "field",
        "from_value",
        "to_value",
    )

    readonly_fields = ('student', "submission",'request', 'from_value', 'to_value', 'field', 'course')

    search_fields = ('student', 'submission', 'course', 'request')

    list_filter = ('student', 'submission', 'course', 'timestamp', 'field', 'from_value', 'to_value')

    actions = [export_as_csv_action()]

    def course(self, obj):
        return format_html('<a href="{}" target="_blank">{}</a>'.format(obj.assignment.url, obj.assignment.course))

    def get_queryset(self, request):
        user_profile = UserProfile.objects.get(user=request.user)
        queryset = SubmissionLog.objects.filter(department=user_profile.department)
        return queryset

admin.site.register(AssignmentLog, AssignmentLogAdmin)
admin.site.register(SubmissionLog, SubmissionLogAdmin)