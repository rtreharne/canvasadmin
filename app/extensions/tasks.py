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
def send_receipt(extension, current_host, root):
    department = extension.assignment.course.course_department
    API_URL = department.CANVAS_API_URL
    API_TOKEN = department.CANVAS_API_TOKEN
    
    canvas = Canvas(API_URL, API_TOKEN)

    student = extension.student

    # Get the student's email address
    student_email = extension.student.login_id

    # Get the assignment name
    assignment_name = extension.assignment.assignment_name

    # Get the course name
    course_name = extension.assignment.course.course_name

    # Get the extension deadline
    extension_deadline = extension.extension_deadline

    # Get the original deadline
    original_deadline = extension.original_deadline

    if root == 'elp':
        label = "exemption from late penalty (ELP)"
    if root == 'extensions':
        label = "extension"

    # Generate a confirmation url from the extension unique_id
    confirmation_url = current_host + '/' + "{}".format(root) + '/confirm/' + "{}".format(extension.confirmation_id)

    message_html = ""
    message_html += "Dear {},\n\n".format(extension.student.sortable_name.split(",")[1].strip())
    message_html += "Your request for an {} has been received and is being processed.\n\n".format(label)
    message_html += "Course: {}\n\n".format(course_name)
    message_html += "Assignment: {}\n\n".format(assignment_name)
    message_html += "Original deadline: {}\n\n".format(original_deadline.strftime("%A, %B %d, %Y at %I:%M %p"))
    message_html += "Extension deadline: {}\n\n".format(extension_deadline.strftime("%A, %B %d, %Y at %I:%M %p"))

    message_html += "Please click the link below to confirm your request (you may need to copy and past the link into your browser).\n\n"
    message_html += "http://{}\n\n".format(confirmation_url)
    
    message_html += "This is an automated message. Please do not reply to this email.\n\n"

        

    # create Canvas conversation
    try:
        conversation = canvas.create_conversation(
            recipients=[extension.student.canvas_id],
            subject="Application for {} confirmation".format(label),
            body=message_html,
            scope="unread",
            context_code="course_{}".format(extension.assignment.course.course_id),
            force_new = True
        )
        return conversation
    except:
        return None
    
@shared_task
def send_approved(extension, root):
    department = extension.assignment.course.course_department
    API_URL = department.CANVAS_API_URL
    API_TOKEN = department.CANVAS_API_TOKEN
    
    canvas = Canvas(API_URL, API_TOKEN)

    # Get the assignment name
    assignment_name = extension.assignment.assignment_name

    # Get the course name
    course_name = extension.assignment.course.course_name

    # Get the extension deadline
    extension_deadline = extension.extension_deadline

    # Get the original deadline
    original_deadline = extension.original_deadline

    print("ROOT: {}".format(root))

    root = root.lower()

    if root == 'elp':
        label = "exemption from late penalty (ELP)"
    if root in ['extensions', 'extension']:
        label = "extension"

    message_html = ""
    message_html += "Dear {},\n\n".format(extension.student.sortable_name.split(",")[1].strip())
    message_html += "Your request for an {} has been approved.\n\n".format(label)
    message_html += "Course: {}\n\n".format(course_name)
    message_html += "Assignment: {}\n\n".format(assignment_name)
    message_html += "Original deadline: {}\n\n".format(original_deadline.strftime("%A, %B %d, %Y at %I:%M %p"))
    message_html += "Extension deadline: {}\n\n".format(extension_deadline.strftime("%A, %B %d, %Y at %I:%M %p"))
    
    message_html += "This is an automated message. Please do not reply to this email.\n\n"

        

    # create Canvas conversation
    try:
        conversation = canvas.create_conversation(
            recipients=[extension.student.canvas_id],
            subject="Application for {} approved".format(label),
            body=message_html,
            scope="unread",
            context_code="course_{}".format(extension.assignment.course.course_id),
            force_new = True
        )
        return conversation
    except:
        return None

@shared_task
def task_apply_overrides(username, extension_pks):
    extensions = Extension.objects.filter(id__in=extension_pks)
    for extension in extensions:
        task_apply_override(username, extension.id, extension.extension_type)

    
@shared_task
def task_apply_override(username, extension_pk, root):
    user = UserProfile.objects.get(user__username=username)
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN

    canvas = Canvas(API_URL, API_TOKEN)

    #try:

    # Determine if any extensions already exist for this student and assignment and delete them.

    extension = Extension.objects.get(pk=extension_pk)

    existing_overrides = [x for x in canvas.get_course(extension.assignment.course.course_id).get_assignment(extension.assignment.assignment_id).get_overrides() 
                            if extension.student.canvas_id in x.__dict__.get("student_ids", [])]

    for override in existing_overrides:
        student_ids = override.__dict__.get("student_ids", [])
        student_ids.remove(extension.student.canvas_id)

        # If this is the last student in the override then delete the override            
        if len(student_ids) == 0:
            override.delete()
        
        # Otherwise, update the override by removing the student from the student_ids list
        else:
            override.edit(
                assignment_override={
                    "student_ids": student_ids
                }
            )

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

    # Send approval email

    conversation = send_approved(extension, root)

    #except:
        #print("override not created!")

def datetime_to_json(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        
    
    

    # handling for if no assignment_id in row
