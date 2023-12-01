from django.contrib import admin
from .models import Staff, ProjectArea, ProjectType, Project, Module, ProjectKeyword, Student
from core.admin_actions import export_as_csv_action
from django.urls import path
import csv
from core.forms import CsvImportForm
from projects.forms import StudentForm
from django.shortcuts import render, redirect
from .models import ProjectKeyword, ProjectArea
from django.db import IntegrityError
from ast import literal_eval
from django.core.exceptions import ObjectDoesNotExist
from .actions import export_project_as_csv, export_student_as_csv
from django.contrib.auth.models import User
from accounts.models import UserProfile

class UsernameFilter(admin.SimpleListFilter):
    title = ('Username')
    parameter_name = 'custom_filter'

    def lookups(self, request, model_admin):
        # Get unique values for the custom filter based on the current user
        return Staff.objects.filter(school=UserProfile.objects.get(user=request.user).department).values_list('username', 'username').distinct().order_by('username')

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(staff__username=self.value())

def read_csv_file(filename):
    rows = []
    with open(filename, 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            rows.append(row)
    return rows

class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "name", "department", "project_area", "keywords", "number", "active", "timestamp")
    list_filter = (UsernameFilter,
                    'timestamp', 
                    'active')
    search_fields = ('staff__username', "staff__surname",)
    actions=['make_inactive', 'make_active', export_project_as_csv]
    list_editable=('number', 'active')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        profile = UserProfile.objects.get(user=request.user)
        department = profile.department
    

        return qs.filter(school=department)

    def username(self, obj):
        return obj.staff.username
    
    def department(self, obj):
        return obj.staff.department
    
    username.admin_order_field = 'staff__username'

    def name(self, obj):
        return ("%s, %s" % (obj.staff.surname, obj.staff.initials))

    def keywords(self, obj):
        string = [x.title for x in obj.project_keyword.all()]
        return string
    
    change_list_template = "projects/projects_changelist.html"
    
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
            
            rows = []
            reader = csv.DictReader(decoded_file)

            for row in reader:
                rows.append(row)

            for row in rows:
                
                # Get prerequisite module
                try:
                    module = Module.objects.get(code=str(row["prerequisite"]))
                except ObjectDoesNotExist:
                    module = None

                # Get Staff
                try:
                    staff = Staff.objects.get(username=row["staff"])
                except ObjectDoesNotExist:
                    staff = None
                
                # Create keywords variable
                keywords = ProjectKeyword.objects.filter(title__in=literal_eval(row["project_keyword"]))

                # Create record
                new_project = Project(
                    title=row["title"],
                    description=row["description"],
                    staff=staff,
                    project_type=ProjectType.objects.get(title=row["project_type"]),
                    project_area=ProjectArea.objects.get(title=row["project_area"]),
                    prerequisite=module,
                    number=row["number"],
                    timestamp=row["timestamp"]
                )

                print(new_project.__dict__)

                new_project.save()

                new_project.project_keyword.set(keywords)

                
                other_type=ProjectType.objects.filter(title__in=literal_eval(row["other_type"]))
                if len(other_type) > 0:
                    new_project.other_type.set(other_type)

                new_project.save()
            
            self.message_user(request, "Your csv file has been imported. Your projects will appear shortly. Keep refreshing.")
            return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(
            request, "csv_form.html", payload
        )
    
    @admin.action(description="Make selected inactive")
    def make_inactive(modeladmin, request, queryset):
        if request.user.is_staff:

            for a in queryset:
                a.active = False
                a.save()

    @admin.action(description="Make selected active")
    def make_active(modeladmin, request, queryset):
        if request.user.is_staff:

            for a in queryset:
                a.active = True
                a.save()


class ProjectKeywordAdmin(admin.ModelAdmin):
    list_display = ("title", "school", "verified")
    list_editable = ("verified",)
    list_filter = ("school",)

    search_fields = ("title",)

    actions = [export_as_csv_action()]

    change_list_template = "projects/projects_changelist.html"
    
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv),
        ]
        return my_urls + urls
    
    def import_csv(self, request):
        if request.method == "POST":
            file = request.FILES["csv_file"]

            if not file.name.endswith('.csv'):
                self.message_user(request, "Your csv file must end with .csv")
                return redirect("..")

            decoded_file = file.read().decode('utf-8').splitlines()

            # read file and skip header row
            reader = csv.reader(decoded_file)
            next(reader)

            # create list of data
            data = []
            for row in reader:
                ProjectKeyword(title=row[0]).save()

            print(data)

            self.message_user(request, "Your csv file has been imported. Your added keywords will appear below.")
            return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(
            request, "csv_form.html", payload
        )

class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'last_name', 'first_name', 'email', 'timestamp', 'school')
    search_fields = ("student_id", "last_name", "first_name", "email")
    list_filter = ("school",)
    list_per_page = 100

    actions= [export_student_as_csv]

    """
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        profile = UserProfile.objects.get(user=request.user)
        department = profile.department
    

        return qs.filter(school=department)
    """

    change_list_template = "projects/student_changelist.html"

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

            # read file and skip header row
            reader = csv.reader(decoded_file)

            # create dictionary of data with student_id as key
            data = {}
            for row in reader:
                data[row[0]] = row[1]

            print(data)

            students = Student.objects.all()

            for student in students:
                try:
                    student.programme = data[student.student_id]
                    student.save()
                except:
                    continue


            self.message_user(request, "Your csv file has been imported. Students will be updated. Keep refreshing.")
            return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(
            request, "csv_form.html", payload
        )

class ProjectAreaAdmin(admin.ModelAdmin):
    
    list_display = ('title', "school")
    search_fields = ("title",)
    list_filter = ("school",)

    actions = [export_as_csv_action()]

    change_list_template = "projects/projects_changelist.html"
    
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv),
        ]
        return my_urls + urls
    
    def import_csv(self, request):
        if request.method == "POST":
            file = request.FILES["csv_file"]

            if not file.name.endswith('.csv'):
                self.message_user(request, "Your csv file must end with .csv")
                return redirect("..")

            decoded_file = file.read().decode('utf-8').splitlines()

            # read file
            # read first row as headers
            rows = []
            reader = csv.DictReader(decoded_file)

            for row in reader:
                rows.append(row)

            for row in rows:
                ProjectArea(title=row["Cognate Areas"]).save()
                
            self.message_user(request, "Your csv file has been imported. Your added project areas will appear below.")
            return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(
            request, "csv_form.html", payload
        )

class ModuleAdmin(admin.ModelAdmin):

    list_display = ('code', 'name', 'school')
    search_fields = ("code", "name")
    list_filter = ("school",)

    actions = [export_as_csv_action()]

    change_list_template = "projects/projects_changelist.html"
    
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv),
        ]
        return my_urls + urls
    
    def import_csv(self, request):
        if request.method == "POST":
            file = request.FILES["csv_file"]

            if not file.name.endswith('.csv'):
                self.message_user(request, "Your csv file must end with .csv")
                return redirect("..")

            decoded_file = file.read().decode('utf-8').splitlines()

            # read file
            # read first row as headers
            rows = []
            reader = csv.DictReader(decoded_file)

            for row in reader:
                rows.append(row)

            print(rows)

            for row in rows:
                Module(code=row["code"], name=row["title"]).save()
                
            self.message_user(request, "Your csv file has been imported. Your added modules will appear below.")
            return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(
            request, "csv_form.html", payload
        )

class StaffAdmin(admin.ModelAdmin):
    list_display = ('surname', 'initials', 'username', 'department', 'number_of_projects')
    search_fields = ("surname", "initials")
    list_filter = ("school","department", "location", "other_location")

    list_editable = ('number_of_projects', )

    actions = [export_as_csv_action()]

    change_list_template = "projects/projects_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv),
            path('update-csv/', self.update_csv),
        ]
        return my_urls + urls

    def update_csv(self, request):
        if request.method == "POST":
            file = request.FILES["csv_file"]

            decoded_file = file.read().decode('utf-8').splitlines()

            # read file and skip header row
            reader = csv.reader(decoded_file)

            # create dictionary of data with username as key
            # the first column is called "search_string", the second is called "username", the third is called "department"
            data = {}
            for row in reader:
                data[row[1]] = {"department": row[2]}

            # update staff department using data
            staff = Staff.objects.all()

            print(data)

            for person in staff:
                try:
                    person.department = data[person.username]["department"]
                    person.save()
                except KeyError:
                    continue

            self.message_user(request, "Your csv file has been imported. Staff will be updated. Keep refreshing.")
            return redirect("..")
        
        form = CsvImportForm()
        payload = {"form": form}
        return render(
            request, "csv_form.html", payload
        )
    
    def import_csv(self, request):
        if request.method == "POST":
            file = request.FILES["csv_file"]

            if not file.name.endswith('.csv'):
                self.message_user(request, "Your csv file must end with .csv")
                return redirect("..")

            decoded_file = file.read().decode('utf-8').splitlines()

            # read file
            # read first row as headers
            rows = []
            reader = csv.DictReader(decoded_file)

            for row in reader:
                rows.append(row)

            print(rows)

            for row in rows:
                try:
                    Staff(username=row["username"],
                          location=row["location"],
                          other_location=row["other_location"],
                          surname=row["surname"], 
                          initials=row["initials"],
                          title=row["title"],
                          preferred_forename=row["preferred_forename"],
                          email=row["email"]).save()
                except IntegrityError:
                    print("Staff already added")
                    continue
                
            self.message_user(request, "Your csv file has been imported. Your added staff will appear below.")
            return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(
            request, "csv_form.html", payload
        )

class ProjectTypeAdmin(admin.ModelAdmin):

    list_display = ('title', 'school')
    search_fields = ("title",)
    list_filter = ("school",)

    actions = [export_as_csv_action()]

    change_list_template = "projects/projects_changelist.html"
    
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv),
        ]
        return my_urls + urls
    
    def import_csv(self, request):
        if request.method == "POST":
            file = request.FILES["csv_file"]

            if not file.name.endswith('.csv'):
                self.message_user(request, "Your csv file must end with .csv")
                return redirect("..")

            decoded_file = file.read().decode('utf-8').splitlines()

            # read file
            # read first row as headers
            rows = []
            reader = csv.DictReader(decoded_file)

            for row in reader:
                rows.append(row)

            for row in rows:
                ProjectType(title=row["Project Types"]).save()
                
            self.message_user(request, "Your csv file has been imported. Your added project types will appear below.")
            return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(
            request, "csv_form.html", payload
        )

# Register your models here.
admin.site.register(Staff, StaffAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(ProjectArea, ProjectAreaAdmin)
admin.site.register(ProjectKeyword, ProjectKeywordAdmin)
admin.site.register(ProjectType, ProjectTypeAdmin)
admin.site.register(Module, ModuleAdmin)



