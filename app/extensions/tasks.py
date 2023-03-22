from __future__ import absolute_import, unicode_literals
from celery import shared_task
from canvasapi import Canvas
from core.models import Course, Assignment, Student, Submission, Staff
from accounts.models import UserProfile
from datetime import datetime, timedelta
from accounts.models import Department
from .models import Extension
from dateutil.parser import parse
import requests


@shared_task
def task_create_extensions(data):
    for row in data:
        task_create_extension(row)

@shared_task
def task_create_extension(row):
    # look for student
    try:
        student = Student.objects.get(sis_user_id__contains=str(row["student_id"]))
    except:
        print("Couldn't find student")
        student = None

    # look for assignment
    if row["assignment_id"] != "":
        assignment = Assignment.objects.get(assignment_id=row["assignment_id"])
        course = assignment.course

        try:
            new_extension = Extension(
                unique_id = row["student_id"],
                student = student,
                course = course,
                assignment = assignment,
                extension_deadline = parse(str(row["extension_deadline"])),
                original_deadline = assignment.due_at
            ).save()
        except:
            print("not created")
    else:
        sub_assignments = Assignment.objects.filter(assignment_name__contains=row["assignment_name"])
        for a in sub_assignments:
            new_row = row.copy()
            new_row["assignment_id"] = a.assignment_id
            task_create_extension(new_row)

@shared_task
def task_apply_overrides(username, extension_pks):
    extensions = Extension.objects.filter(id__in=extension_pks)
    for extension in extensions:
        task_apply_override(username, extension)

    
@shared_task
def task_apply_override(username, extension):
    user = UserProfile.objects.get(user__username=username)
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN

    canvas = Canvas(API_URL, API_TOKEN)

    try:

        assignment = canvas.get_course(extension.assignment.course.course_id).get_assignment(extension.assignment.assignment_id)

        
        assignment.create_override(
            assignment_override={
                "student_ids": [extension.student.canvas_id],
                "due_at": datetime_to_json(extension.extension_deadline)
            }
        )


        extension.approved = True
        extension.approved_by = user
        extension.approved_on = datetime.now()
        extension.save()

    except:
        print("override not created")

def datetime_to_json(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        
    
    

    # handling for if no assignment_id in row
