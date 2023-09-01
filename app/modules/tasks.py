from __future__ import absolute_import, unicode_literals
import requests
from celery import shared_task
from canvasapi import Canvas
from core.models import Course, Assignment, Student, Submission, Staff
from accounts.models import UserProfile
from datetime import datetime, timedelta
from accounts.models import Department
from .models import Module

def json_to_datetime(dt):
    try:
        return datetime.strptime(dt, "%Y-%m-%dT%H:%M:%SZ")
    except:
        print("couldn't convert datetime")
        return None
    
@shared_task
def get_modules(username, course_ids, search_string):
    user = UserProfile.objects.get(user__username=username)
    prefixes = user.department.course_prefixes.replace(" ", "").split(",")
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN
    canvas = Canvas(API_URL, API_TOKEN)

    for c in course_ids:
        try:
            course = canvas.get_course(c)
            modules = [x for x in course.get_modules() if x.name.lower() == search_string.lower()]
            for module in modules:
                Module(
                    name = module.name,
                    course = Course.objects.get(course_id=course.id),
                    module_id = module.id,
                    unlock_at = module.unlock_at,
                    published = module.published
                ).save()
                print("Module saved!")
        except:
            continue
    
    return "Completed"

@shared_task
def task_update_modules(username, module_ids, time_string, publish=None):
    for module_id in module_ids:
        task_update_module(username, module_id, time_string, publish=publish)
    return "Done"

@shared_task
def task_update_module(username, module_id, time_string, publish=None):
        
    user = UserProfile.objects.get(user__username=username)
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN

    canvas = Canvas(API_URL, API_TOKEN)
    
    module = Module.objects.get(pk=module_id)
    print("course_id", module.course.course_id, "publish", publish)
    canvas_course = canvas.get_course(module.course.course_id)
    canvas_module = canvas_course.get_module(module.module_id)

    canvas_module.edit(module={"unlock_at": time_string, "published": publish})
    
    module.unlock_at = json_to_datetime(time_string)
    if publish is not None:
        module.published = publish
    module.save()
    print("module saved!")






