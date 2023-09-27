from django.contrib import admin
from django.utils.html import format_html
from accounts.models import User, UserProfile
from canvasapi import Canvas
from core.models import Sample, Course, Assignment, Student, Submission, Staff, Date
from .tasks import *
from django.contrib.admin import DateFieldListFilter
from .tasks import update_assignments, get_courses, task_update_assignment_deadlines, task_assign_markers, task_apply_zero_scores, task_award_five_min_extensions, task_copy_to_resit_course, task_assign_resit_course_to_courses, task_make_only_visible_to_overrides, task_create_assignment_summary, task_enroll_teachers_on_resit_course
from logs.models import AssignmentLog, Department
from .admin_actions import export_as_csv_action
from django.contrib import messages
from .filters import AssignmentDateFilter, SubmissionDateFilter, PreviousDateFilter
from datetime import datetime
from .forms import CsvImportForm, AssignmentDatesUpdateForm, AssignResitForm
from django.urls import path
import csv
from django.shortcuts import render, redirect
from admin_confirm.admin import AdminConfirmMixin, confirm_action
from .helpers import *

class StaffAdmin(admin.ModelAdmin):
    list_display = ("name", "items_graded", "courses_graded_in",)

    list_filter = ("name",)

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

    actions = ["admin_get_assignments_by_course",
               "admin_get_enrollments_by_course",
                export_as_csv_action(),
                "organise_assignments",
                "hide_totals",
                "assign_resit_course",
                #"enroll_teachers_on_resit_course",
                #"create_assignment_summary"
    ]

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
            print(data)

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

    @admin.action(description="Get enrollments for selected")
    def admin_get_enrollments_by_course(modeladmin, request, queryset):
        if request.user.is_staff:
            course_ids = [x.course_id for x in queryset]
            task_get_enrollments_by_courses.delay(request.user.username, course_ids)
            messages.info(request, "Getting Enrollments! This action is not instantaneous. Please check back later.")

    def assign_resit_course(self, request, queryset):
        print("Hi rob", request.POST)
        if 'apply'in request.POST:
            print("Hello World", request.POST)
            resit_course_pk = request.POST.get("resit_course", None)
            if resit_course_pk is not None:
                resit_course_pk = int(resit_course_pk)
            course_pks = [x.id for x in queryset]
            print("course_pks", course_pks)
            task_assign_resit_course_to_courses.delay(request.user.username, course_pks, resit_course_pk)
            self.message_user(request, "Your request has been submitted. Your assignments will update shortly. Keep refreshing.")
            return redirect(".")
        form = AssignResitForm()
        payload = {'form': form, 'courses': queryset}
        return render(
            request, "core/assign_resit_course_form.html", payload
        )
    
    @admin.action(description="Organise assignments")
    def organise_assignments(modeladmin, request, queryset):
        if request.user.is_staff:
            course_ids = [x.course_id for x in queryset]
            for course_id in course_ids:
                task_organise_assignments.delay(request.user.username, course_id)
            messages.info(request, "Organising Assignments! This action is not instantaneous. Please check back later.")
        
    @admin.action(description="Hide totals from students")
    def hide_totals(modeladmin, request, queryset):
        if request.user.is_staff:
            course_ids = [x.course_id for x in queryset]
            for course_id in course_ids:
                task_hide_totals.delay(request.user.username, course_id)
            messages.info(request, "Hiding totals! This action is not instantaneous. Please check back later.")


    @admin.action(description="Create Assignment Summary Page")
    def create_assignment_summary(modeladmin, request, queryset):
        if request.user.is_staff:
            course_ids = [x.course_id for x in queryset]
            for course_id in course_ids:
                task_create_assignment_summary.delay(request.user.username, course_id)
            messages.info(request, "Creating Assignment Summary! This action is not instantaneous. Please check back later.")
    
    @admin.action(description="Enroll Teachers On Resit Course")
    def enroll_teachers_on_resit_course(modeladmin, request, queryset):
        if request.user.is_staff:
            course_ids = [x.course_id for x in queryset]
            for course_id in course_ids:
                task_enroll_teachers_on_resit_course.delay(request.user.username, course_id)
            messages.info(request, "Enrolling Teachers on Resit Course! This action is not instantaneous. Please check back later.")


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

    actions = [export_as_csv_action(),]


class SecondsLateFilter(admin.SimpleListFilter):
    title = 'Late Filter'
    parameter_name = 'seconds_late'

    def lookups(self, request, model_admin):
        return (
            ('less_than_five_min', 'Less than 5 mins late'),
            ('more_than_five_min', 'More than 5 mins late'),
            ('more_than_five_days', 'More than 5 days late')
        )

    def queryset(self, request, queryset):
        value = self.value()

        if value == 'less_than_five_min':
            return queryset.filter(seconds_late__gte = 1, seconds_late__lte=300)
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
            ('ungraded', 'Not Graded'),
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
        elif value == 'ungraded':
            return queryset.filter(score=None)
        
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


class SubmissionAdmin(AdminConfirmMixin, admin.ModelAdmin):
    list_per_page=500

    list_display = (
        "student_link",
        "course",
        "submission_link",
        "score",
        "marker_grader",
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
        "student__sortable_name", "assignment__assignment_name", "assignment__course__course_code"
    )

    actions = ["sync_submissions", "apply_zero_scores", "apply_cat_b", "apply_cat_c", 
               export_as_csv_action(), "award_five_min_extensions"]

    change_list_template = "core/submissions_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('assign-markers/', self.import_csv),
        ]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            file = request.FILES["csv_file"]

            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.reader(decoded_file)

            print(reader)

            data = []
            
            [data.append(x) for x in reader]
            headers = data[0]
            data = data[1:]
            print(headers)

            rows = []

            for row in data:
                rows.append(
                    {x: y for x, y in zip(headers, row)}
                )

            task_assign_markers(request.user.username, data=rows)



            #get_courses.delay(request.user.username, courses=data)

            
            self.message_user(request, "Your csv file has been imported. Your submissions will be updates shortly. Keep refreshing.")
            return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(
            request, "csv_form.html", payload
        )
    
    def get_queryset(self, request):
        user_profile = UserProfile.objects.get(user=request.user)
        queryset = Submission.objects.filter(course__course_department=user_profile.department)
        return queryset

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
        
    def marker_grader(self, obj):
        if obj.marker != None:
            return format_html('<a href="mailto:{}">{}</a>'.format(obj.marker_email, obj.marker))
        elif obj.graded_by == None:
            return "-"
        else:
            return obj.graded_by
        
        return "{}/{}".format(obj.marker, obj.graded_by)

    def similarity_link(self, obj):
        if obj.similarity_score != None:
            return format_html('<a href="{}" target="_blank">{}</a>'.format(obj.turnitin_url, obj.similarity_score))
        return None

    def days_late(self,obj):
        return float("{:.2f}".format(float(obj.seconds_late/(3600*24))))

    days_late.admin_order_field = "seconds_late"

    similarity_link.short_description = "Similarity Score (%)"
    similarity_link.admin_order_field = "similarity_score"

    marker_grader.short_description = "Marker"
    
    submission_link.short_description = "Submission"
    submission_link.admin_order_field = "assignment"

    student_link.short_description="Student"
    student_link.admin_order_field = "student"

    @admin.action(description="Sync selected submissions")
    @confirm_action
    def sync_submissions(modeladmin, request, queryset):
        if request.user.is_staff:
            user_profile = UserProfile.objects.get(user=request.user)
            
            submission_ids = [x.submission_id for x in queryset]

            # break submission_ids into batches of max 100
            submission_ids_batch = [submission_ids[i:i + 100] for i in range(0, len(submission_ids), 100)]



            for submission_ids in submission_ids_batch:
                update_submissions.delay(request.user.username, submission_ids)

    
            messages.info(request, "Syncing submissions. This action is not instantaneous. Check back later.")
    
    @admin.action(description="Apply zero scores to selected")
    @confirm_action
    def apply_zero_scores(modeladmin, request, queryset):
        if request.user.is_staff:
            user_profile = UserProfile.objects.get(user=request.user)

            submission_ids = [x.id for x in queryset]

            task_apply_zero_scores.delay(request.user.username, submission_ids)
            messages.info(request, "Apply zero scores. This action is not instantaneous. Check back later.")

    @admin.action(description="Apply Category B Cap")
    @confirm_action
    def apply_cat_b(modeladmin, request, queryset):
        if request.user.is_staff:
            user_profile = UserProfile.objects.get(user=request.user)
            submission_ids = [x.id for x in queryset]
            task_apply_cat_bs.delay(request.user.username, submission_ids)
            messages.info(request, "Apply Cat B Cap. This action in not instantaneous. Check back later.")
        
    @admin.action(description="Apply Category C Cap")
    @confirm_action
    def apply_cat_c(modeladmin, request, queryset):
        if request.user.is_staff:
            user_profile = UserProfile.objects.get(user=request.user)
            submission_ids = [x.id for x in queryset]
            task_apply_cat_cs.delay(request.user.username, submission_ids)
            messages.info(request, "Apply Cat C Cap. This action in not instantaneous. Check back later.")

    @admin.action(description="Award 5 min extensions")
    @confirm_action
    def award_five_min_extensions(modeladmin, request, queryset):
        if request.user.is_staff:
            user_profile = UserProfile.objects.get(user=request.user)
            submission_ids = [x.id for x in queryset]
            task_award_five_min_extensions.delay(request.user.username, submission_ids)
            messages.info(request, "Awarding 5 min extensions. This action in not instantaneous. Check back later.")


class GradedFilter(admin.SimpleListFilter):
    title = 'Grading Status'
    parameter_name = 'pc_graded'

    def lookups(self, request, model_admin):
        return (
            ('outstanding', 'Outstanding'),
            ('completed', 'Completed'),
            ('no_submissions', 'No Submissions'),
            ('has_submissions', 'Has Submissions'),
            ('not_graded', 'Not Graded')
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
        elif value == 'not_graded':
            return queryset.filter(pc_graded=0).exclude(pc_graded=None)
        #return queryset


class AssignmentAdmin(AdminConfirmMixin, admin.ModelAdmin):
    list_display = (
        "assignment_link",
        #"assignment_name",
        "link",
        "due_at",
        "posted_at",
        "graded_pc",
        "average_score",
        "anonymous_grading",
        "published",
        "active",
        "quiz",
        "previous_deadline",
    )

    #list_filter = ('')

    #readonly_fields = ('assignment_name','course', 'assignment_id', 'url', 'unlock_at', 'due_at', 'lock_at', 'needs_grading_count', 'published', 'anonymous_grading')

    actions = ["admin_anonymise", 
               "admin_deanonymise", 
               export_as_csv_action(), 
               "sync_assignments", 
               "get_submissions", 
               "task_add_five_minutes_to_deadlines", 
               "update_assignment_deadlines", 
               "make_inactive",
               "make_active",
               "duplicate_for_resit",
               "copy_to_resit_course",
               "make_only_visible_to_overrides",
               "assign_to_next_term",
               "copy_to_next_term",
               "find_last_term_assignment",
               ]

    list_editable = ('active', 'quiz')

    search_fields = ('assignment_name', 'course__course_code')

    list_filter = (
                   'course__course_code',
                   'assignment_name',
                   GradedFilter,
                   'active',
                   'quiz',
                   'published',
                   AssignmentDateFilter,
                   'has_overrides',
                   'anonymous_grading',
                   PreviousDateFilter)
    
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

            deadline_date = request.POST.get("deadline_date", None)
            deadline_time = request.POST.get("deadline_time", None)

            lock_date = request.POST.get("lock_date", None)
            lock_time = request.POST.get("lock_time", None)

            publish = request.POST.get("force_publish", None)

            only_visible_to_overrides = request.POST.get("only_visible_to_overrides", None)

            unlock_time_string = unlock_date + "T" + unlock_time + ":00Z"
            deadline_time_string = deadline_date + "T" + deadline_time + ":00Z"
            lock_time_string = lock_date + "T" + lock_time + ":00Z"

            assignment_pks = [x.id for x in queryset]
            task_update_assignment_deadlines.delay(request.user.username, assignment_pks, unlock_time_string, deadline_time_string, lock_time_string, only_visible_to_overrides)
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
    
    def previous_deadline(self, obj):
        try:
            return obj.previous_term_assignment.due_at
        except:
            return None

    def assignment_link(self, obj):
        return format_html('<a href="{}" target="_blank">{} ...</a> <a href="{}/change">[edit]</a>'.format(obj.url, obj.assignment_name[:25], obj.id))


    def link(self, obj):
        return format_html('<a href="{}/courses/{}/grades" target="_blank">{}</a>'.format(obj.department.CANVAS_API_URL, obj.course.course_id, obj.course))
    
    assignment_link.short_description = "Assignment Name"
    assignment_link.admin_order_field = "assignment_name"
    link.short_description = "Course"
    link.admin_order_field = 'course__course_code'

        
    def graded_pc(self, obj):
        submissions = Submission.objects.filter(assignment = obj)
        if len(submissions) > 0:
            graded_string = ""
            if obj.pc_graded != None:
                graded_string += str(obj.pc_graded)
                graded_string += " (" + str(obj.graded) + "/" + str(len(submissions)) + ")" 
            url = "/admin/core/submission/?assignment_id={}".format(obj.id)
            return format_html("<a href='{}'>{}</a>".format(url, graded_string))
        return obj.pc_graded
    
    graded_pc.short_description = "Graded (%)"
    graded_pc.admin_order_field = 'pc_graded'

    
    @admin.action(description="Make selected inactive")
    def make_inactive(modeladmin, request, queryset):
        if request.user.is_staff:
            user_profile = UserProfile.objects.get(user=request.user)

            for a in queryset:
                a.active = False
                a.save()

    @admin.action(description="Make selected active")
    def make_active(modeladmin, request, queryset):
        if request.user.is_staff:
            user_profile = UserProfile.objects.get(user=request.user)

            for a in queryset:
                a.active = True
                a.save()
    
    @admin.action(description="Anonymize selected assignments")
    @confirm_action
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
    @confirm_action
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
            for assignment_id in assignment_ids:
                task_get_submissions.delay(request.user.username, [assignment_id])
            messages.info(request, "Getting Submissions. This action is not instantaneous. Please check back later.")

    @admin.action(description="Add five minutes to selected deadlines")
    @confirm_action
    def task_add_five_minutes_to_deadlines(modeladmin, request, queryset):
        if request.user.is_staff:
            assignment_ids = [x.assignment_id for x in queryset]
            add_five_minutes_to_deadlines.delay(request.user.username, assignment_ids)

            messages.info(request, "Adding five minutes to deadlines. This action is not instantaneous. Please check back later.")

    @admin.action(description="Duplicate for resit")
    @confirm_action
    def duplicate_for_resit(modeladmin, request, queryset):
        if request.user.is_staff:
            assignment_ids = [x.assignment_id for x in queryset]
            for assignment_id in assignment_ids:
                task_duplicate_for_resit.delay(request.user.username, assignment_id)
            messages.info(request, "Duplicating for resit. This action is not instantaneous. Please check back later.")
    
    @admin.action(description="Copy to resit course")
    @confirm_action
    def copy_to_resit_course(modeladmin, request, queryset):
        if request.user.is_staff:
            assignment_ids = [x.assignment_id for x in queryset]
            for assignment_id in assignment_ids:
                task_copy_to_resit_course.delay(request.user.username, assignment_id)
            messages.info(request, "Copying to resit course. This action is not instantaneous. Please check back later.")

    @admin.action(description="Make selected only visible to overrides")
    @confirm_action
    def make_only_visible_to_overrides(modeladmin, request, queryset):
        if request.user.is_staff:
            assignment_ids = [x.assignment_id for x in queryset]
            for assignment_id in assignment_ids:
                task_make_only_visible_to_overrides.delay(request.user.username, assignment_id)
            messages.info(request, "Making assignments only visible to overrides. This action is not instantaneous. Please check back later.")

    @admin.action(description="Assign to next term course")
    @confirm_action
    def assign_to_next_term(modeladmin, request, queryset):
        if request.user.is_staff:
            assignment_ids = [x.assignment_id for x in queryset]
            for assignment_id in assignment_ids:
                task_assign_to_next_term.delay(request.user.username, assignment_id)
            messages.info(request, "Assigning to next term course. This action is not instantaneous. Please check back later.")

    @admin.action(description="Copy to next term course")
    @confirm_action
    def copy_to_next_term(modeladmin, request, queryset):
        if request.user.is_staff:
            assignment_ids = [x.assignment_id for x in queryset]
            for i, assignment_id in enumerate(assignment_ids):
                task_copy_to_next_term_course.delay(request.user.username, assignment_id)
            messages.info(request, "Copying to next term course. This action is not instantaneous. Please check back later.")

    @admin.action(description="Find last term assignment")
    @confirm_action
    def find_last_term_assignment(modeladmin, request, queryset):
        if request.user.is_staff:
            for assignment in queryset:
                try:
                    term = find_first_match(term_pattern, assignment.course.course_code)
                    print(term)
                    last_term = int(term) - 101
                    print(last_term)
                    last_course = Course.objects.get(course_code = assignment.course.course_code.replace(term, str(last_term)))
                    print(last_course)

                    label = find_first_match(assignment_pattern, assignment.assignment_name)
                    print("label", label)
                
                    last_term_assignment = Assignment.objects.filter(course=last_course, assignment_name__contains=label)[0]
                    assignment.previous_term_assignment = last_term_assignment
                    assignment.save()
                except:
                    print("No last term assignment found")
                    last_term_assignment = None


class DateAdmin(admin.ModelAdmin):
    list_display = ("label", "start", "finish")
            

admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Date, DateAdmin)
