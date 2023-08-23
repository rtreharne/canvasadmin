from django.shortcuts import render, redirect
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db import IntegrityError
import os
from itertools import chain
from .models import Staff, Project, ProjectKeyword, Student, ProjectArea, ProjectType
from .forms import StaffForm, ProjectForm, ExistingStaffForm, StudentForm
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
today = datetime.now().date() - timedelta(days=100)

INSTITUTE = (
        ('1', 'Ageing and Chronic Disease'),
        ('2', 'Human Anatomy Resource Centre'),
        ('3', 'Infection and Global Health'),
        ('4', 'Integrative Biology'),
        ('5', 'Liverpool School of Tropical Medicine'),
        ('6', 'School of Life Sciences'),
        ('7', 'Translational Medicine'),
        ('8', 'Other'),
    )
DEPARTMENT = (
        ('1', 'Eye and Vision Science'),
        ('2', 'Musculoskeletal Biology I'),
        ('3', 'Musculoskeletal Biology II'),
        ('4', 'Clinical Infection, Microbiology and Immunology'),
        ('5', 'Epidemiology and Population Health'),
        ('6', 'Infection Biology'),
        ('7', 'Biochemistry'),
        ('8', 'Evolution, Ecology and Behaviour'),
        ('9', 'Funtional and Comparative Genomics'),
        ('10', 'Clinical Sciences'),
        ('11', 'International Public Health'),
        ('12', 'Parasitology'),
        ('13', 'Vector Biology'),
        ('14', 'Biostatistics'),
        ('15', 'Cellular and Molecular Physiology'),
        ('16', 'Molecular and Clinical Cancer Medicine'),
        ('17', 'Molecular Pharmacology'),
        ('18', "Women's and Children's Health"),
        ('19', "Not applicable (SOLS, HARC etc)"),
        ('20', "Other"),
    )

def index(request):
    return render(request, 'projects/index.html')

def returning_staff(request):

    if request.method == "POST":


        form = ExistingStaffForm(request.POST)
        if form.is_valid():
            staff = Staff.objects.get(username=form.cleaned_data['username'])
            projects = Project.objects.filter(staff=staff).order_by("-pk")#distinct("title", "active")


            existing_staff_form = ExistingStaffForm()
            existing_staff_form['username'].initial = staff.username

            return render(request, "projects/staff_dash.html", {'projects': projects,
                                                        'form': existing_staff_form,
                                                        'staff': staff})


    else:
        form = ExistingStaffForm()


    return render(request, "projects/returning-staff.html", {'form': form})


def staff_project(request):
    if request.method == "POST":
        form = ExistingStaffForm(request.POST)

        if form.is_valid():
            staff = Staff.objects.get(username=form.cleaned_data['username'])
            staff.username = staff.username.lower()
            project_form = ProjectForm()
            project_form['staff'].initial = staff
            return render(request, "projects/project.html", {'form': project_form,
                                                     'staff': staff})

    else:
        form = StaffForm()

    return render(request, "staff.html", {'form': form})


def project_details(request):

    if request.method == "POST":

        form = ProjectForm(request.POST)

        if form.is_valid():
            staff = form.cleaned_data["staff"]

            print(form.cleaned_data)

            if form.cleaned_data["suggested_keyword"] != None:

                inst = form.save(commit=False)

                keywords_string = form.cleaned_data["suggested_keyword"].lower()
                keywords_list = keywords_string.split(',')
                keywords_list = [x.strip().capitalize() for x in keywords_list]
                for word in keywords_list:
                    if word != "":
                        try:
                            ProjectKeyword.objects.create(
                                title=word,
                                verified=False
                            )
                        except:
                            continue


                keyword_objs = ProjectKeyword.objects.filter(title__in=keywords_list)
                print(keyword_objs)
                print(form.cleaned_data["project_keyword"])

                project_keyword = form.cleaned_data["project_keyword"]#.union(keyword_objs)
                #project_keyword = form.cleaned_data["project_keyword"]

                inst.save()
                inst.project_keyword.add(*project_keyword)
                inst.project_keyword.add(*keyword_objs)
            else:
                form.save()

            projects = Project.objects.filter(staff=staff)
            staff = Staff.objects.get(id=staff.id)

            existing_staff_form = ExistingStaffForm()
            existing_staff_form['username'].initial = staff.username
            return render(request, "projects/staff_dash.html", {"form": existing_staff_form,
                                                       "projects": projects,
                                                       "staff": staff})
    else:
        form = ProjectForm()

    return render(request, "projects/project.html", {'form': form})


def use_again(request, id):

    try:
        project = Project.objects.get(pk=id)
    except:
        return redirect('index')
    form = ProjectForm(instance=project)

    return (render(request, "projects/project.html", {"form": form,
                                              "flag": True}))


def edit_project(request, id):

    try:
        project = Project.objects.get(id=id)
        staff = Staff.objects.get(id=project.staff.id)
    except:
        return redirect('/projects/index')

    if request.method == "POST":
        form = ProjectForm(request.POST or None, instance=project)
        if form.is_valid():
            form.save()
            projects = Project.objects.filter(staff=staff)

            existing_staff_form = ExistingStaffForm()
            existing_staff_form['username'].initial = staff.username
            return render(request, "projects/staff_dash.html", {"form": existing_staff_form,
                                                        "projects": projects,
                                                        "staff": staff})
        else:
            form.add_error(None, "You have chosen too many/too few keywords or other types of project. Your project has not been saved. Make changes and click 'Submit'.")
            return render(request, "projects/edit_project.html", {"form": form,
                                                         "staff": staff,
                                                         "project": id})

    form = ProjectForm(instance=project)


    return render(request, "projects/edit_project.html", {"form": form,
                                                  "staff": staff,
                                                  "project": id})


def staff_details(request):

    if request.method == "POST":
        form = StaffForm(request.POST)
        if form.is_valid():
            form.save()
            staff = Staff.objects.get(username=form.cleaned_data['username'])
            staff.username = staff.username.lower()
            project_form = ProjectForm()
            project_form['staff'].initial = staff
            return render (request, "projects/project.html", {'form': project_form,
                                                      'staff': staff})

    else:
        form = StaffForm()

    return render(request, "projects/staff.html", {'form': form})


def tandc(request):
    return render(request, "projects/terms_and_conditions.html")

def privacy(request):

    return render(request, "projects/privacy_policy.html")

def check_unique_set(request, key):

    obj_list = [request.POST["{0}_{1}".format(key, x)] for x in range(1, 6)]

    if len(set(obj_list)) < 5:
        print(len(set(obj_list)))
        return False

    print(len(set(obj_list)))

    return True

def student(request):

    if request.method == "POST":
        print("GOT HERE")


        form = StudentForm(request.POST)

        print("Keywords Unique", check_unique_set(request, "project_keyword"))
        print("Types Unique", check_unique_set(request, "project_type"))


        if check_unique_set(request, "project_keyword") and check_unique_set(request, "project_type"):
            print("I'm getting through the unique check")

            

            if form.is_valid():
                print("form is valid!")
                try:
                    inst = form.save()
                except IntegrityError:
                    form.add_error(None, "UNIQUE")



                return redirect('projects:student-thanks')
            
            print("form is not valid!")
            print(form.errors)

        else:
            print("form is not valid!")

            form.add_error(None, "Error")

            return render(request, "projects/student_form.html", {"form": form})

    else:

        form = StudentForm()

    return render(request, "projects/student_form.html", {"form": form})



def student_thanks(request):

    return render(request, "projects/student_thanks.html")