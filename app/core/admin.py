from django.contrib import admin
from django.utils.html import format_html
from accounts.models import User, UserProfile
from canvasapi import Canvas
from core.models import Sample, Course, Assignment, Student, Submission, Staff, Date
from .tasks import anonymise_assignments, deanonymise_assignments, task_get_submissions, update_submissions, get_assignments_by_courses, add_five_minutes_to_deadlines
from django.contrib.admin import DateFieldListFilter
from .tasks import update_assignments, get_courses, task_update_assignment_deadlines
from logs.models import AssignmentLog, Department
from .admin_actions import export_as_csv_action
from django.contrib import messages
from .filters import AssignmentDateFilter, SubmissionDateFilter
from datetime import datetime
from .forms import CsvImportForm, AssignmentDatesUpdateForm
from django.urls import path
import csv
from django.shortcuts import render, redirect

class StaffAdmin(admin.ModelAdmin):
    list_display = ("name", "items_graded", "courses_graded_in",)

admin.site.register(Staff, StaffAdmin)


class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "course_code",
        "course_id",
        "course_department"
    )

    search_fields = (
        "course_code",
    )

    actions = ["admin_get_assignments_by_course",]

    change_list_template = "core/courses_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv),
        ]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            file = request.FILES["csv_file"]

            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.reader(decoded_file)

            data = []
            [data.extend(x) for x in reader]

            get_courses.delay(request.user.username, courses=data)

            
            self.message_user(request, "Your csv file has been imported. Your courses will appear shortly. Keep refreshing.")
            return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(
            request, "csv_form.html", payload
        )

    def get_queryset(self, request):
        user_profile = UserProfile.objects.get(user=request.user)
        queryset = Course.objects.filter(course_department=user_profile.department)
        return queryset

    @admin.action(description="Get assignments for selected")
    def admin_get_assignments_by_course(modeladmin, request, queryset):
        if request.user.is_staff:
            course_ids = [x.course_id for x in queryset]
            get_assignments_by_courses.delay(request.user.username, course_ids)
            messages.info(request, "Getting Assignments! This action is not instantaneous. Please check back later.")

class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "sortable_name",
        "sis_user_id",
        "canvas_id",
        "login_id"
    )

    search_fields = (
        "sortable_name",
    )


class SecondsLateFilter(admin.SimpleListFilter):
    title = 'Late Filter'
    parameter_name = 'seconds_late'

    def lookups(self, request, model_admin):
        return (
            ('late', 'Late'),
            ('less_than_five_min', 'Less than 5 mins late'),
            ('more_than_five_min', 'More than 5 mins late'),
            ('more_than_five_days', 'More than 5 days late')
        )

    def queryset(self, request, queryset):
        value = self.value()

        if value == 'late':
            return queryset.filter(seconds_late__gt = 0)
        elif value == 'less_than_five_min':
            return queryset.filter(seconds_late__gt = 0, seconds_late__lte=300)
        elif value == 'more_than_five_min':
            return queryset.filter(seconds_late__gt=300)
        elif value == 'more_than_five_days':
            return queryset.filter(seconds_late__gt=3600*24*5)
        
        return queryset


class ScoreFilter(admin.SimpleListFilter):
    title = 'Score Filter'
    parameter_name = 'score'

    def lookups(self, request, model_admin):
        return (
            ('zero', 'Zero'),
            ('greater_than_zero', 'Greater than zero'),
            ('less_than_forty', 'Less than 40'),
            ('less_than_fifty', 'Less than 50')
        )

    def queryset(self, request, queryset):
        value = self.value()

        if value == 'zero':
            return queryset.filter(score=0)
        elif value == 'greater_than_zero':
            return queryset.filter(score__gt=0)
        elif value == 'less_than_forty':
            return queryset.filter(score__lt=40)
        elif value == 'less_than_fifty':
            return queryset.filter(score__lt=50)
        
        return queryset


class IntegrityConcernFilter(admin.SimpleListFilter):
    title = 'Integrity Flag'
    parameter_name = 'integrity_concern'

    def lookups(self, request, model_admin):
        return (
            ('a', 'A'),
            ('b', 'B'),
            ('c_d_or_e', 'C, D or E'),
            ('has_concern', 'Any'),
            ('-', '-')
        )

    def queryset(self, request, queryset):
        value = self.value()

        if value == 'a':
            return queryset.filter(integrity_concern="A").exclude(integrity_concern=None)
        elif value == 'b':
            return queryset.filter(integrity_concern="B").exclude(integrity_concern=None)
        elif value == 'c_d_or_e':
            return queryset.filter(integrity_concern="C, D or E").exclude(integrity_concern=None)
        elif value == 'has_concern':
            return queryset.exclude(integrity_concern=None)
        elif value == '-':
            return queryset.filter(integrity_concern=None)
        return queryset


class SubmissionAdmin(admin.ModelAdmin):
    list_per_page=500

    list_display = (
        "student_link",
        "course",
        "submission_link",
        "score",
        "graded_by",
        "submitted_at",
        "days_late",
        "posted_at",
        "integrity_concern",
        "similarity_link"
    )

    list_filter=("assignment__course__course_code", 
                 "assignment__assignment_name",
                 "student__sortable_name",
                 SubmissionDateFilter,
                 ScoreFilter,
                 SecondsLateFilter,
                 IntegrityConcernFilter,
                 )

    search_fields = (
        "student__sortable_name", "assignment__assignment_name",
    )

    actions = ["sync_submissions", export_as_csv_action(),]

    def student_link(self, obj):
        return format_html('<a href="?student__sortable_name={}">{}</a>'.format(obj.student, obj.student))

    def submission_link(self, obj):
        if not obj.assignment.anonymous_grading:
            return format_html('<a href="{}/courses/{}/gradebook/speed_grader?assignment_id={}&student_id={}" target="_blank">{}</a>'.format(
                obj.assignment.department.CANVAS_API_URL,
                obj.assignment.course.course_id,
                obj.assignment.assignment_id, 
                obj.student.canvas_id,
                obj.assignment.assignment_name)
                )
        else:
            return obj.assignment.assignment_name

    def similarity_link(self, obj):
        if obj.similarity_score != None:
            return format_html('<a href="{}" target="_blank">{}</a>'.format(obj.turnitin_url, obj.similarity_score))
        return None

    def days_late(self,obj):
        return float("{:.2f}".format(float(obj.seconds_late/(3600*24))))

    days_late.admin_order_field = "seconds_late"

    similarity_link.short_description = "Similarity Score (%)"
    similarity_link.admin_order_field = "similarity_score"
    
    submission_link.short_description = "Submission"
    submission_link.admin_order_field = "assignment"

    student_link.short_description="Student"
    student_link.admin_order_field = "student"

    @admin.action(description="Sync selected submissions")
    def sync_submissions(modeladmin, request, queryset):
        if request.user.is_staff:
            user_profile = UserProfile.objects.get(user=request.user)
            
            submission_ids = [x.submission_id for x in queryset]
        
            update_submissions.delay(request.user.username, submission_ids)
            messages.info(request, "Syncing submissions. This action is not instantaneous. Check back later.")

    
class GradedFilter(admin.SimpleListFilter):
    title = 'Grading Status'
    parameter_name = 'pc_graded'

    def lookups(self, request, model_admin):
        return (
            ('outstanding', 'Outstanding'),
            ('completed', 'Completed'),
            ('no_submissions', 'No Submissions'),
            ('has_submissions', 'Has Submissions')
        )

    def queryset(self, request, queryset):
        value = self.value()
        print("Printing Value:", value)

        if value == 'outstanding':
            return queryset.filter(pc_graded__lt=100).exclude(pc_graded=None)
        elif value == 'completed':
            print("completed")
            return queryset.filter(pc_graded=100.0).exclude(pc_graded=None)
        elif value == 'no_submissions':
            return queryset.filter(pc_graded=None)
        elif value == 'has_submissions':
            return queryset.filter(pc_graded__gte=0).exclude(pc_graded=None)
        #return queryset


class AssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "assignment_link",
        "link",
        "due_at",
        "has_overrides",
        "graded_pc",
        "average_score",
        "anonymous_grading",
        "published",
        #"active",
        #"sas_exam"
    )

    #list_filter = ('')

    #readonly_fields = ('assignment_name','course', 'assignment_id', 'url', 'unlock_at', 'due_at', 'lock_at', 'needs_grading_count', 'published', 'anonymous_grading')

    actions = ["admin_anonymise", "admin_deanonymise", export_as_csv_action(), "sync_assignments", "get_submissions", "task_add_five_minutes_to_deadlines", "update_assignment_deadlines"]

    #list_editable = ('active', 'sas_exam')

    search_fields = ('assignment_name', 'course__course_code')

    list_filter = (
                   'course__course_code',
                   'assignment_name',
                   GradedFilter,
                   'active',
                   'sas_exam',
                   'published',
                   AssignmentDateFilter,
                   'has_overrides')
    
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('update-assignment-deadline/', self.update_assignment_deadlines),
        ]
        return my_urls + urls
    
    def update_assignment_deadlines(self, request, queryset):
        if 'apply' in request.POST:

            module_pks = request.POST.get("_selected_action")
            unlock_date = request.POST.get("unlock_date", None)
            unlock_time = request.POST.get("unlock_time", None)
            publish = request.POST.get("force_publish", None)

            time_string = unlock_date + "T" + unlock_time + ":00Z"
            assignment_pks = [x.id for x in queryset]
            task_update_assignment_deadlines.delay(request.user.username, assignment_pks, time_string)
            self.message_user(request, "Your request has been submitted. Your assignments will update shortly. Keep refreshing.")
            return redirect(".")
        form = AssignmentDatesUpdateForm()
        payload = {'form': form, 'assignments': queryset}
        return render(
            request, "core/assignment_dates_update_form.html", payload
        )

    
    def get_queryset(self, request):
        user_profile = UserProfile.objects.get(user=request.user)
        queryset = Assignment.objects.filter(course__course_department=user_profile.department)
        return queryset

    def assignment_link(self, obj):
        return format_html('<a href="{}" target="_blank">{}</a>'.format(obj.url, obj.assignment_name))


    def link(self, obj):
        return format_html('<a href="{}/courses/{}/grades" target="_blank">{}</a>'.format(obj.department.CANVAS_API_URL, obj.course.course_id, obj.course))
    
    assignment_link.short_description = "Assignment Name"
    assignment_link.admin_order_field = "assignment_name"
    link.short_description = "Course"
    link.admin_order_field = 'ascending'

        
    def graded_pc(self, obj):
        submissions = Submission.objects.filter(assignment = obj)
        if len(submissions) > 0:
            graded_string = ""
            if obj.pc_graded != None:
                graded_string = obj.pc_graded
            url = "/core/submission/?assignment__assignment_name={}".format(obj.assignment_name)
            return format_html("<a href='{}'>{}</a>".format(url, graded_string))
        return obj.pc_graded
    
    graded_pc.short_description = "Graded (%)"
    graded_pc.admin_order_field = 'pc_graded'

    
    
    
    @admin.action(description="Anonymize selected assignments")
    def admin_anonymise(modeladmin, request, queryset):
        if request.user.is_staff:
            user_profile = UserProfile.objects.get(user=request.user)

            for a in queryset:
                a.anonymous_grading = True
                a.save()

            API_URL = user_profile.department.CANVAS_API_URL
            API_TOKEN = user_profile.department.CANVAS_API_TOKEN

            course_assignments = [{"course_id": x.course.course_id, "assignment_id": x.assignment_id} for x in queryset]

            anonymise_assignments.delay(course_assignments, API_URL, API_TOKEN)

            AssignmentLog(
                            assignment=a.assignment_name,
                            course=a.course,
                            request="UPDATE",
                            field="anonymous_grading",
                            from_value=False,
                            to_value=True
                        ).save()
   
    
    @admin.action(description="De-anonymise selected assignments")
    def admin_deanonymise(modeladmin, request, queryset):
        if request.user.is_staff:
            user_profile = UserProfile.objects.get(user=request.user)

            for a in queryset:
                a.anonymous_grading = False
                a.save()

            API_URL = user_profile.department.CANVAS_API_URL
            API_TOKEN = user_profile.department.CANVAS_API_TOKEN

            course_assignments = [{"course_id": x.course.course_id, "assignment_id": x.assignment_id} for x in queryset]

            deanonymise_assignments.delay(course_assignments, API_URL, API_TOKEN)

        
    @admin.action(description="Sync selected assignments")
    def sync_assignments(modeladmin, request, queryset):
        if request.user.is_staff:
            user_profile = UserProfile.objects.get(user=request.user)
            
            assignment_ids = [x.assignment_id for x in queryset]
        
            update_assignments.delay(request.user.username, assignment_ids)
            messages.info(request, "Syncing Assignments. This action is not instantaneous. Please check back later.")

    
    @admin.action(description="Get submissions")
    def get_submissions(modeladmin, request, queryset):
        if request.user.is_staff:
            assignment_ids = [x.assignment_id for x in queryset]
            task_get_submissions.delay(request.user.username, assignment_ids)
            messages.info(request, "Getting Submissions. This action is not instantaneous. Please check back later.")

    @admin.action(description="Add five minutes to selected deadlines")
    def task_add_five_minutes_to_deadlines(modeladmin, request, queryset):
        if request.user.is_staff:
            assignment_ids = [x.assignment_id for x in queryset]
            add_five_minutes_to_deadlines.delay(request.user.username, assignment_ids)
            messages.info(request, "Adding five minutes to deadlines. This action is not instantaneous. Please check back later.")

class DateAdmin(admin.ModelAdmin):
    list_display = ("label", "start", "finish")
            

admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Date, DateAdmin)
