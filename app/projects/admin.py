from django.contrib import admin
from .models import Staff, ProjectArea, ProjectType, Project, Module, ProjectKeyword, Student
from core.admin_actions import export_as_csv_action
from django.urls import path
import csv
from core.forms import CsvImportForm
from django.shortcuts import render, redirect
from .models import ProjectKeyword, ProjectArea
from django.db import IntegrityError
from ast import literal_eval
from django.core.exceptions import ObjectDoesNotExist

def read_csv_file(filename):
    rows = []
    with open(filename, 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            rows.append(row)
    return rows

class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "title", "project_area", "keywords", "number", "timestamp")
    search_fields = ("id", "staff__surname")


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


class ProjectKeywordAdmin(admin.ModelAdmin):
    list_display = ("title", "verified")
    list_editable = ("verified",)

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
    list_display = ('student_id', 'last_name', 'first_name', 'email', 'timestamp')
    search_fields = ("student_id", "last_name")
    list_per_page = 500

class ProjectAreaAdmin(admin.ModelAdmin):
    
    list_display = ('title',)
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

    list_display = ('code', 'name',)
    search_fields = ("code", "name")

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
    list_display = ('surname', 'initials', 'email')
    search_fields = ("surname", "initials")

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

    list_display = ('title',)
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



