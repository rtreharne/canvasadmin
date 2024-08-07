from django.contrib import admin
from .models import Extension, Date
from .forms import CsvImportForm
from django.urls import path
import csv
from django.shortcuts import render, redirect
from .tasks import task_create_extensions, task_apply_overrides
from .admin_actions import export_as_csv_action
from accounts.models import UserProfile
from django.utils.html import format_html
from django.contrib import messages
from .filters import DateFilter
from django.http import HttpResponseRedirect

class ExtensionAdmin(admin.ModelAdmin):
    list_display = (
        "unique_id",
        "student",
        "extension_type",
        "course",
        "assignment_link",
        "original_deadline",
        "extension_deadline",
        "approved",
        "status",
        "approved_by",
        "evidence",
        "submitted_at",
        "updated_at"
    )

    list_filter = (
        "student",
        "assignment",
        "extension_type",
        "status",
        "course",
        DateFilter
        
    )

    # make field "status" read only
    readonly_fields = ("status", "submitted_at")

    """
    def get_queryset(self, request):
        user_profile = Extension.objects.get(user=request.user)
        queryset = Extension.objects.filter(assignment__course_department=user_profile.department)
        return queryset
    """

    change_list_template = "extensions/extensions_changelist.html"

    actions = [export_as_csv_action(), "apply_overrides"]

    

    def assignment_link(self, obj):
        return format_html('<a href="{}" target="_blank">{}</a>'.format(obj.assignment.url, obj.assignment.assignment_name))
    
    assignment_link.short_description = "Assignment Name"
    assignment_link.admin_order_field = "assignment__assignment_name"

    def course(self, obj):
        return obj.assignment.course
        return format_html('<a href="{}/courses/{}/grades" target="_blank">{}</a>'.format(obj.department.CANVAS_API_URL, obj.course.course_id, obj.course))
    
    course.short_description = "Course"
    course.admin_order_field = "assignment_course"
    
    def evidence(self, obj):
        if obj.files:
            return format_html('<a href="{}" target="_blank">Download</a>'.format(obj.files.url))
        else:
            return None
    
    evidence.short_description = "Evidence"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv),
        ]
        return my_urls + urls

    def import_csv(self, request):
        template = "/static/static/extensions/csv_templates/extension_template.csv"
        info = "<p>Your csv file must have columns 'student_id', 'extension_type', 'assignment_id' and 'extension_deadline'.</p><p><a href='{}'>Download template csv</a></p>".format(template)
        if request.method == "POST":
            file = request.FILES["csv_file"]

            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.reader(decoded_file)


            data = []
            
            [data.append(x) for x in reader]
            headers = data[0]
            data = data[1:]

            # remove blank rows (might contain "," only)
            data = [x for x in data if x != []]


            rows = []

            for row in data:
                rows.append(
                    {x: y for x, y in zip(headers, row)}
                )

            task_create_extensions(rows)

            
            self.message_user(request, "Your csv file has been imported. Your extensions will appear shortly. Keep refreshing.")
            return redirect("..")
        form = CsvImportForm()
        payload = {"form": form, "info": info}
        return render(
            request, "extensions/csv_form.html", payload
        )
    
    def response_change(self, request, obj):
        if "_save" in request.POST:
            return HttpResponseRedirect(request.path)
        return super().response_change(request, obj)
    
    @admin.action(description="Approve and apply overrides to selected")
    def apply_overrides(modeladmin, request, queryset):
        if request.user.is_staff:

            extension_pks = [x.pk for x in queryset]
            task_apply_overrides.delay(request.user.username, extension_pks)

            messages.info(request, "Your overrides are being created in Canvas. Check back later to confirm success.")

            # Update "updated_at" field
            queryset.update()

        


admin.site.register(Extension, ExtensionAdmin)
admin.site.register(Date)