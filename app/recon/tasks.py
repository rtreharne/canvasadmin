from __future__ import absolute_import, unicode_literals
import requests
from celery import shared_task
from core.models import Course, Assignment, Student, Submission, Staff
from datetime import datetime, timedelta
from .models import CourseMarker

def json_to_datetime(dt):
    try:
        return datetime.strptime(dt, "%Y-%m-%dT%H:%M:%SZ")
    except:
        print("couldn't convert datetime")
        return None

@shared_task
def submission_recon(submission_ids):
    submissions = Submission.objects.filter(id__in=submission_ids)

    print(submissions[0].__dict__.keys())

    courses = list(set([x.assignment.course for x in submissions]))
    print(courses)

    for course in courses:
        course_submissions = submissions.filter(assignment__course=course)

        course_staff = list(set([x.graded_by for x in course_submissions if x.graded_by != None]))

        for staff in course_staff:
            graded_count = course_submissions.filter(graded_by=staff).count()

            try:
                course_marker = CourseMarker.objects.get(course=course, grader=staff)
                course_marker["graded_count"] = graded_count
                course_marker.save()
            except:
                CourseMarker(
                    course=course,
                    grader=staff,
                    graded_count=graded_count
                ).save()

