from __future__ import absolute_import, unicode_literals
from logs.models import AssignmentLog, SubmissionLog
import requests
from celery import shared_task
from canvasapi import Canvas
from .models import Course, Assignment, Student, Submission, Staff
from enrollments.models import Enrollment
from accounts.models import UserProfile
from datetime import datetime, timedelta
from accounts.models import Department
from celery.utils.log import get_task_logger
import time
import re
from .helpers import *


logger = get_task_logger(__name__)

# schedule tasks
# get assignments
# get submissions
# update submissions
# update assignments

def json_to_datetime(dt):
    try:
        return datetime.strptime(dt, "%Y-%m-%dT%H:%M:%SZ")
    except:
        print("couldn't convert datetime")
        return None

@shared_task
def add(x, y):
    return x + y

@shared_task
def anonymise_assignments(assignments, API_URL, API_TOKEN):
    canvas = Canvas(API_URL, API_TOKEN)
    for a in assignments:
        try:
            course = canvas.get_course(a["course_id"])
            print(course)
            assignment = course.get_assignment(a["assignment_id"])
            print(assignment)
        except:
            print("Couldn't find course or assignment")
            return False
        

        try:
            assignment.edit(assignment={"anonymous_grading": True})
            #return "Canvas successfully updated"
        except:
            print("Couldn't update canvas")

            aobject = Assignment.objects.get(assignment_id=a["assignment_id"])
            department = aobject.department
            aobject.anonymous_grading=False
            aobject.save()

            AssignmentLog(
                            assignment=assignment.name,
                            course=course.course_code,
                            request="UPDATE",
                            field="anonymous_grading",
                            from_value=False,
                            to_value=True,
                            department=department
                        ).save()
            

    return "Done: Anonymising Assignments"

@shared_task
def deanonymise_assignments(assignments, API_URL, API_TOKEN):
    canvas = Canvas(API_URL, API_TOKEN)
    for a in assignments:
        try:
            course = canvas.get_course(a["course_id"])
            print(course)
            assignment = course.get_assignment(a["assignment_id"])
            print(assignment)
        except:
            print("Couldn't find course or assignment")
            return False
        

        try:
            assignment.edit(assignment={"anonymous_grading": False})
            #return "Canvas successfully updated"
        except:
            print("Couldn't update canvas")

            aobject = Assignment.objects.get(assignment_id=a["assignment_id"])
            department = aobject.department
            aobject.anonymous_grading=True
            aobject.save()

            AssignmentLog(
                            assignment=assignment.name,
                            course=course.course_code,
                            request="UPDATE",
                            field="anonymous_grading",
                            from_value=True,
                            to_value=False,
                            department=department
                        ).save()
            

    return "Done: Anonymising Assignments"

@shared_task
def get_courses(username, term=None, courses=None):

    user = UserProfile.objects.get(user__username=username)
    prefixes = user.department.course_prefixes.replace(" ", "").split(",")
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN
    canvas = Canvas(API_URL, API_TOKEN)

    if courses != None:
        for c in courses:
            try:

                course = canvas.get_course(c, use_sis_id=True)

                Course(
                        course_code=course.course_code,
                        course_id = course.id,
                        course_name = course.name,
                        course_department = user.department
                        ).save()
                print(course.course_code, "saved!")
            except:
                print("There was an issue")
                continue
        return "Courses Added!"


    if term != None:
        for prefix in prefixes:
            for i in range(101, 1000):
                try:
                    course_code = "{}{}-{}".format(prefix.upper(), str(i), str(term))
                    print(course_code)
                    course = canvas.get_course(course_code, use_sis_id=True)
                    Course(
                        course_code=course.course_code,
                        course_id = course.id,
                        course_name = course.name,
                        course_department = user.department
                    ).save()
                    print(course.course_code, "saved!")
                except:
                    continue

@shared_task
def get_course(username, course):
    pass

def get_submission_summary(API_URL, API_TOKEN, course_id, assignment_id):
    url = API_URL + "/api/v1/courses/{}/assignments/{}/submission_summary".format(course_id, assignment_id)
    print(url)

    headers = {'Authorization': 'Bearer ' + API_TOKEN}

    r = requests.get(url, headers= headers)
    return r.json()

@shared_task
def task_get_all_assignments(username):
    user = UserProfile.objects.get(user__username=username)
    courses = Course.objects.filter(course_department = user.department)
    course_ids = [x.course_id for x in courses]
    get_assignments_by_courses.delay(username, course_ids)

@shared_task
def get_all_submissions(username):
    user = UserProfile.objects.get(user__username=username)
    assignments = Assignment.objects.filter(department=user.department, active=True)
    assignment_ids = [x.assignment_id for x in assignments]
    task_get_submissions.delay(username, assignment_ids)


@shared_task
def update_all_assignments(username):
    user = UserProfile.objects.get(user__username=username)
    assignments = Assignment.objects.filter(department=user.department)
    assignment_ids = [x.assignment_id for x in assignments]
    update_assignments.delay(username, assignment_ids)

@shared_task
def update_all_submissions(username):
    user = UserProfile.objects.get(user__username=username)
    submissions = [x for x in Submission.objects.filter(department=user.department) if x.assignment.active]
    submission_ids = [x.submission_id for x in submissions]
    update_submissions.delay(username, submission_ids)

@shared_task
def get_assignments_by_courses(username, course_ids):
    for course_id in course_ids:
        get_assignments_by_course(username, course_id)

@shared_task
def get_assignments_by_course(username, course_id):
    user = UserProfile.objects.get(user__username=username)
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN
    canvas = Canvas(API_URL, API_TOKEN)

    course = canvas.get_course(course_id)
    c = Course.objects.get(course_id=course_id)

    assignments = [x for x in course.get_assignments()]
    for assignment in assignments:
        summary = get_submission_summary(API_URL, API_TOKEN, course.id, assignment.id)
        if "online_upload" in assignment.submission_types:
            quiz=False
        else:
            quiz=True

        try:
            pc_graded = float("{:.2f}".format(100*summary["graded"]/(summary["graded"]+summary["ungraded"])))
        except:
            pc_graded = None

        try:
            rubric_title = f"{assignment.rubric_settings['title']} - {assignment.rubric_settings['id']}"
        except:
            rubric_title = None

        try:
            Assignment(
                department = user.department,
                assignment_name = assignment.name[:128],
                course = c,
                assignment_id = assignment.id,
                unlock_at = json_to_datetime(assignment.unlock_at),
                lock_at = json_to_datetime(assignment.lock_at),
                due_at = json_to_datetime(assignment.due_at),
                url = assignment.html_url,
                needs_grading_count = assignment.needs_grading_count,
                published = assignment.published,
                anonymous_grading = assignment.anonymous_grading,
                active = True,
                graded = summary["graded"],
                ungraded = summary["ungraded"],
                pc_graded = pc_graded,
                not_submitted = summary["not_submitted"],
                quiz=quiz,
                rubric_title = rubric_title

            ).save()
            print("Assignment saved")
        except:
            continue


@shared_task
def get_assignments(username):
    user = UserProfile.objects.get(user__username=username)
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN
    canvas = Canvas(API_URL, API_TOKEN)

    courses = Course.objects.filter(course_department = user.department)
    
    for c in courses:
        #try:
        course = canvas.get_course(c.course_id)

        assignments = [x for x in course.get_assignments()]
        for assignment in assignments:
            try:
                summary = get_submission_summary(API_URL, API_TOKEN, course.id, assignment.id)
                print(summary)
                try:
                    pc_graded = float("{:.2f}".format(100*summary["graded"]/(summary["graded"]+summary["ungraded"])))
                except:
                    pc_graded = None

                
                Assignment(
                    department = user.department,
                    assignment_name = assignment.name[:128],
                    course = c,
                    assignment_id = assignment.id,
                    unlock_at = json_to_datetime(assignment.unlock_at),
                    lock_at = json_to_datetime(assignment.lock_at),
                    due_at = json_to_datetime(assignment.due_at),
                    url = assignment.html_url,
                    needs_grading_count = assignment.needs_grading_count,
                    published = assignment.published,
                    anonymous_grading = assignment.anonymous_grading,
                    active = True,
                    graded = summary["graded"],
                    ungraded = summary["ungraded"],
                    pc_graded = pc_graded,
                    not_submitted = summary["not_submitted"],
                    has_overrides = assignment.has_overrides,

                    ).save()
                print("Assignment saved")
            except:
            #print("course doesn't exist")
                continue


@shared_task()
def update_all_assignments(username):
    user = UserProfile.objects.get(user__username=username)
    assignment_ids = [x.assignment_id for x in Assignment.objects.filter(department=user.department)]
    update_assignments(username, assignment_ids)


@shared_task()
def update_assignments(username, assignment_ids):
    user = UserProfile.objects.get(user__username=username)
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN
    canvas = Canvas(API_URL, API_TOKEN)

    assignments = Assignment.objects.filter(assignment_id__in=assignment_ids)




    # Look for submissions
    for assignment in assignments:
        try:
            submissions = Submission.objects.filter(assignment=assignment)
            scores = [x.score for x in submissions if x.score != None]
            average_score = sum(scores)/len(scores)
            print("POINTS POSSIBLE", assignment.points_possible)
            if assignment.points_possible != None:
                assignment.average_score = round(100*(average_score/assignment.points_possible), 1)
            else:
                assignment.average_score = round(average_score, 1)

            # Get most common "posted_at" value
            print("UPDATING POSTED_AT")
            posted_at = [x.posted_at for x in submissions if x.posted_at != None]
            
            assignment.posted_at = max(set(posted_at), key = posted_at.count)
            
            assignment.save()
        except:
            continue

    app_canvas_mapp = {
        "assignment_name": "name",
        "unlock_at": "unlock_at",
        "lock_at": "lock_at",
        "due_at": "due_at",
        "needs_grading_count": "needs_grading_count",
        "published": "published",
        "anonymous_grading": "anonymous_grading",
        "type": "submission_types",
        "has_overrides": "has_overrides",
        "points_possible": "points_possible",
    }

    for a in assignments:
        # get canvas assignment
        
        try:
            canvas_assignment = canvas.get_course(a.course.course_id).get_assignment(a.assignment_id)
            assignment_found = True
        except:
            assignment_found = False

        if assignment_found:

            # try and update rubric_title (lazy)
            try:
                rubric_title = f"{canvas_assignment.rubric_settings['title']} - {canvas_assignment.rubric_settings['id']}"
            except:
                rubric_title = None

            a.rubric_title = rubric_title

            for key, value in app_canvas_mapp.items(): 
                

                datetime = is_datetime(canvas_assignment.__dict__.get(key, None))
                    
                if datetime:

                    if key == "due_at":
                        if canvas_assignment.has_overrides:
                            canvas_assignment = canvas.get_course(a.course.course_id).get_assignment(a.assignment_id, all_dates=True)
                            try:
                                for item in canvas_assignment.all_dates:
                                    if 'base' in item and item['base']:
                                        datetime = is_datetime(item['due_at'])
                            except:
                                print(canvas_assignment.__dict__)
                                pass
                        
                    if len(str(a.__dict__[key])) <1:
                        pass
                    else:
                        
                        print(key, "updated")
                        
                        AssignmentLog(
                            assignment=a.assignment_name,
                            course=a.course,
                            request="UPDATE",
                            field=key,
                            from_value=str(a.__dict__[key]),
                            to_value=str(datetime),
                            department=user.department
                        ).save()

                        setattr(a, key, datetime)
                        
                        a.save()
                else:
                    if (canvas_assignment.__dict__[value] != a.__dict__[key]) or (canvas_assignment.__dict__[value]==0):
                        if key == "needs_grading_count":
                            summary = get_submission_summary(API_URL, API_TOKEN, course_id=a.course.course_id, assignment_id=a.assignment_id)
                            print("I'M TRYING TO UPDATE THE GRADING COUNTS")
                            print(summary)

                            try:
                                pc_graded = float("{:.2f}".format(100*summary["graded"]/(summary["graded"]+summary["ungraded"])))
                            except:
                                pc_graded = None
                            
                            a.graded = summary["graded"]
                            a.ungraded = summary["ungraded"]
                            a.not_submitted = summary["not_submitted"]
                            
                            AssignmentLog(
                            assignment=canvas_assignment.__dict__["name"],
                            course=a.course,
                            request="UPDATE",
                            field=key,
                            from_value=str(a.__dict__["pc_graded"]),
                            to_value=str(pc_graded),
                            department=user.department
                            ).save()

                            try:    
                                pc_graded = float("{:.2f}".format(100*a.graded/(a.graded+a.ungraded)))
                            except:
                                pc_graded = 0

                            a.pc_graded = pc_graded
                            a.save()




                        if key == "assignment_name":
                            logs = AssignmentLog.objects.filter(assignment=a, course=a.course)
                            for log in logs:
                                setattr(log, "assignment", canvas_assignment.__dict__["name"])
                                log.save()
                            pass


                        print(key, "updated")
                        AssignmentLog(
                            assignment=canvas_assignment.__dict__["name"][:120],
                            course=a.course,
                            request="UPDATE",
                            field=key,
                            from_value=str(a.__dict__[key]),
                            to_value=str(canvas_assignment.__dict__[value]),
                            department=user.department
                            ).save()

                        print(key, value, canvas_assignment.__dict__[value], a.__dict__[key])
                        setattr(a, key, canvas_assignment.__dict__[value])
                        try:    
                            a.pc_ungraded = float("{:.2f}".format(100*a.graded/(a.graded+a.ungraded)))
                        except:
                            a.pc_ungraded = 0
                        a.save()
                    
                    
        #except:
           #AssignmentLog(
                            #assignment=a.assignment_name,
                            #course=a.course,
                            #request="DELETE",
                            #field="",
                            #from_value="",
                            #to_value="",
                            #department=user.department
                        #).save()
            # assignment not found. Delete assignment on app?
            #print("assignment not found!")
            #a.delete()

def is_datetime(dt):
    try:
        return datetime.strptime(dt, "%Y-%m-%dT%H:%M:%SZ")
    except:
        return False

@shared_task()
def task_get_submissions(username, assignment_ids):
    print("assignment_ids", assignment_ids)
    assignments = Assignment.objects.filter(assignment_id__in=assignment_ids)
    assignment_ids = [x.assignment_id for x in assignments if x.active]
    for assignment_id in assignment_ids:
        task_get_submission(username, assignment_id)

@shared_task()
def task_get_submission(username, assignment_id):
    assignment = Assignment.objects.get(assignment_id=assignment_id)

    #if assignment.graded == 0:
        #return None

    user = UserProfile.objects.get(user__username=username)
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN
    canvas = Canvas(API_URL, API_TOKEN)
    assessment_exists = True

    try:
        c = canvas.get_course(assignment.course.course_id)
        a = c.get_assignment(assignment.assignment_id)
    except:
        assessment_exists = False

    if assessment_exists:

        submissions = [x for x in a.get_submissions(include=["assignment", "user", "submission_comments", "full_rubric_assessment", "submission_history"])]

        missing_students = False
        enrollments = False

        for sub in submissions:
            try:
                student = Student.objects.get(canvas_id=sub.user["id"])
            except:
                missing_students=True

        
        if missing_students:
            enrollments = [x for x in c.get_enrollments() if x.type=="StudentEnrollment"]

            for e in enrollments:
                try:
                    
                    student = Student.objects.get(canvas_id=e.user_id)
                    print("student exists!")
                except:
                    
                    new_student = Student(
                        sortable_name=e.user["sortable_name"],
                        canvas_id=int(e.user_id),
                        login_id=e.user["login_id"],
                        sis_user_id=e.user["sis_user_id"]
                    )
                    new_student.save()

        for sub in submissions:
            

            # Does submission already exist?
            new_submission = Submission.objects.filter(submission_id=sub.id)

            print("checking submissions", sub.user["sortable_name"], sub.submitted_at, len(new_submission))


            if len(new_submission) == 0:

                if sub.submitted_at != None:

                    # look for category concerns
                    concerns = {
                        "category a": "A",
                        "category b": "B",
                        "category c": "C, D or E"
                    }

                    gai_declaration = {
                        "did not use GAI": "Did not use GAI",
                        "using GAI": "Using GAI",
                        "did not include": "No declaration"
                    }
                    
                    integrity_flag = None
                    gai_flag = None
                    staff_exists = True

                    if sub.grader_id != None:
                        try:
                            staff = Staff.objects.get(canvas_id=sub.grader_id)
                            graded_by = staff.name
                        except:
                            staff_exists = False
                    
                    if not staff_exists:
                        try:
                            if int(sub.grader_id) > 0:
                                canvas_user = canvas.get_user(sub.grader_id)
                                staff = Staff(
                                    name=canvas_user.sortable_name,
                                    canvas_id=sub.grader_id
                                ).save()
                                
                                graded_by = canvas_user.sortable_name
                            else:
                                graded_by = "Auto Graded"
                        except:
                            graded_by = None
                    else:
                        graded_by = None
                    
                    try: 
                        
                        for key in concerns:
                            rubric_data = sub.full_rubric_assessment["data"]
                            for item in rubric_data:
                                if key in item['description'].lower():
                                    integrity_flag = concerns[key]
                    except:
                        integrity_flag = None

                    try:
                        for key in gai_declaration:
                            rubric_data = sub.full_rubric_assessment["data"]
                            for item in rubric_data:
                                if key in item['description'].lower():
                                    gai_flag = gai_declaration[key]
                    except:
                        gai_flag = None

                    try:
                        score=float('{0:.2f}'.format(sub.score))
                    except:
                        score=None

                    try:
                        posted_at = json_to_datetime(sub.posted_at)
                    except:
                        posted_at = None

                    try:
        
                        turnitin_data_key = list(sub.turnitin_data.keys())[0]
            
                        similarity_score = float(sub.turnitin_data[turnitin_data_key]["similarity_score"])
            
                        turnitin_url = API_URL + sub.turnitin_data[turnitin_data_key]["report_url"]
            
                    except:
                        similarity_score = None
                        turnitin_url = None

                    try:
                        rubric = sub.full_rubric_assessment
                    except:
                        rubric=None

                    if assignment.points_possible != None:
                        try:    
                            score = float('{0:.1f}'.format(100*score/assignment.points_possible))
                        except:
                            score = None
                    
    

                    try:
                        new_submission =Submission(
                        student=Student.objects.get(canvas_id=sub.user_id),
                        sis_user_id=Student.objects.get(canvas_id=sub.user_id).sis_user_id,
                        submission_id=sub.id,
                        submitted_at=json_to_datetime(sub.submitted_at),
                        assignment=assignment,
                        course=assignment.course,
                        score=score,
                        integrity_concern = integrity_flag,
                        gai_declaration = gai_flag,
                        posted_at = posted_at,
                        similarity_score = similarity_score,
                        turnitin_url = turnitin_url,
                        graded_by = graded_by,
                        comments = sub.submission_comments,
                        rubric = rubric,
                        seconds_late = sub.seconds_late,
                        html_url="{}/courses/{}/gradebook/speed_grader?assignment_id={}&student_id={}".format(API_URL, assignment.course.course_id, assignment.assignment_id, sub.user_id) 
                        )
                        new_submission.save()
                        print("submission_added")
                        print("submission_history:", sub.submission_history)

                        # Check for SpLDs
                        if student.support_plan:
                            # Get number of sub attempts
                            attempts = sub.attempt
                            if attempts == None or attempts == 1:
                                attempt = 1
                                sub.edit(comment={"text_comment":student.marker_message, "attempt": attempt})
                                print("SpLD message added (on first submission)")
                            else:
                                attempt = attempts
                                sub.edit(comment={"text_comment":student.marker_message, "attempt": attempt})
                                print("SpLD message added (on most recent submission)")
                    except:
                        print("submission not added")
            


@shared_task()
def update_submissions(username, submission_ids):
    user = UserProfile.objects.get(user__username=username)
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN
    canvas = Canvas(API_URL, API_TOKEN)

    submissions = Submission.objects.filter(submission_id__in=submission_ids, assignment__active=True)

    app_canvas_mapp = {
        "score": "score",
        "seconds_late": "seconds_late",
    }

    

    for i, sub in enumerate(submissions):

        # Does student have sis_user_id?
        

        try:
            canvas_submission = canvas.get_course(sub.assignment.course.course_id).get_assignment(sub.assignment.assignment_id).get_submission(sub.student.canvas_id, include=["user", "submission_comments", "full_rubric_assessment", "submission_history"])
        except:
            print("couldn't get canvas submission")
            continue

        if sub.submitted_at != None:

            # look for category concerns
            concerns = {
                "category a": "A",
                "category b": "B",
                "category c": "C, D or E"
            }

            gai_declaration = {
                        "did not use GAI": "Did not use GAI",
                        "using GAI": "Using GAI",
                        "did not include": "No declaration"
                    }

            integrity_flag = None
            gai_flag = None    
            
            try:
                for key in concerns:
                    rubric_data = canvas_submission.full_rubric_assessment["data"]
                    for item in rubric_data:
                        if key in item['description'].lower():
                            integrity_flag = concerns[key]
                
                if sub.integrity_concern != integrity_flag:
                    print("updating integrity flag")
                    SubmissionLog(
                                student=sub.student,
                                submission=sub.assignment,
                                course=sub.assignment.course.course_code,
                                request="UPDATE",
                                field="integrity_flag",
                                from_value=str(sub.integrity_concern),
                                to_value=str(integrity_flag),
                                department=user.department
                                ).save()
                    sub.integrity_concern = integrity_flag
                    sub.save()
            except:
                continue

            try:
                for key in gai_declaration:
                    rubric_data = canvas_submission.full_rubric_assessment["data"]
                    for item in rubric_data:
                        if key in item['description'].lower():
                            gai_flag = gai_declaration[key]
                
                sub.gai_declaration = gai_flag
                sub.save()
            except:
                sub.gai_declaration = None
     
        
        if sub.student.sis_user_id == None:

            try:
                sis_user_id = canvas_submission.user["sis_user_id"]
                student = sub.student
                student.sis_user_id = sis_user_id
                student.save()
                sub.sis_user_id = sis_user_id
                sub.save()
                print("updated sis_user_id")
            except:
                print("couldn't update sis_user_id")

        if sub.sis_user_id == None:
            try:
                sub.sis_user_id = sub.student.sis_user_id
                sub.save()
            except:
                print("couldn't get sis_user_id")

        if canvas_submission.grader_id != None:
            try:
                staff = Staff.objects.get(canvas_id=canvas_submission.grader_id)
                graded_by = staff.name
            except:
                if int(canvas_submission.grader_id) > 0:
                    canvas_user = canvas.get_user(canvas_submission.grader_id)
                    staff = Staff(
                        name=canvas_user.sortable_name,
                        canvas_id=canvas_submission.grader_id
                    ).save()
                    
                    graded_by = canvas_user.sortable_name
                else:
                    graded_by = "Auto Graded"
        else:
            graded_by = None

        try:
            comments = canvas_submission.submission_comments
        except:
            comments = None

        try:
            rubric = canvas_submission.full_rubric_assignment
        except:
            rubric = None

        print(app_canvas_mapp)

        for key, value in app_canvas_mapp.items():

            canvas_value = canvas_submission.__dict__[value]
        
            if key == "score":
                assignment = Assignment.objects.get(assignment_id=sub.assignment.assignment_id)
                print("assignment.points_possible", assignment.points_possible)
                print(canvas_value)
                if assignment.points_possible != None:
                    try:
                        canvas_value = float('{0:.1f}'.format(100*float(canvas_value)/assignment.points_possible))
                    except:
                        print("couldn't convert to percentage!")

            print(sub.__dict__[key], canvas_value)

            if sub.__dict__[key] != canvas_value:

                print("updating_submission")                

                SubmissionLog(
                            student=sub.student,
                            submission=sub.assignment,
                            course=sub.assignment.course.course_code,
                            request="UPDATE",
                            field=key,
                            from_value=str(sub.__dict__[key]),
                            to_value=str(canvas_value),
                            department=user.department
                            ).save()
    
                setattr(sub, key, canvas_value)
            sub.graded_by = graded_by
            sub.comments = comments
            sub.rubric = rubric
            sub.html_url="{}/courses/{}/gradebook/speed_grader?assignment_id={}&student_id={}".format(API_URL, sub.assignment.course.course_id, sub.assignment.assignment_id, sub.student.canvas_id)

            sub.save()

                
@shared_task()
def add_five_minutes_to_deadlines(username, assignment_ids):
    for assignment_id in assignment_ids:
        add_five_minutes_to_deadline(username, assignment_id)

@shared_task()
def add_five_minutes_to_deadline(username, assignment_id):
    user = UserProfile.objects.get(user__username=username)
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN
    canvas = Canvas(API_URL, API_TOKEN)

    assignment = Assignment.objects.get(assignment_id=assignment_id)

    try:
        canvas_assignment = canvas.get_course(assignment.course.course_id).get_assignment(assignment.assignment_id)
        due_at = json_to_datetime(canvas_assignment.due_at)
        new_due_at = due_at + timedelta(minutes=5)
        new_due_at_string = datetime_to_json(new_due_at)
        new_lock_at = json_to_datetime(canvas_assignment.lock_at) + timedelta(minutes=5)
        if canvas_assignment.due_at == canvas_assignment.lock_at:
            new_lock_at_string = datetime_to_json(new_lock_at)
            canvas_assignment.edit(assignment={"lock_at": new_lock_at_string})
            assignment.lock_at = new_lock_at
            AssignmentLog(
                assignment=canvas_assignment.__dict__["name"],
                course=assignment.course,
                request="UPDATE",
                field="lock_at",
                from_value=canvas_assignment.lock_at,
                to_value=new_lock_at_string,
                department=user.department  
            ).save()
            assignment.save()

        AssignmentLog(
            assignment=canvas_assignment.__dict__["name"],
            course=assignment.course,
            request="UPDATE",
            field="due_at",
            from_value=canvas_assignment.due_at,
            to_value=new_due_at_string,
            department=user.department
            ).save()

        canvas_assignment.edit(assignment={"due_at": new_due_at_string})
        assignment.due_at = new_due_at
        assignment.save()
        print("deadline was extended by five minutes")

    except:
        print("Couldn't extend deadline")


def datetime_to_json(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

@shared_task()
def task_assign_resit_course_to_courses(username, course_pks, resit_course_id):
    for course_pk in course_pks:
        task_assign_resit_course_to_course(username, course_pk, resit_course_id)
    return "Done"

@shared_task()
def task_assign_resit_course_to_course(username, course_pk, resit_course_id):
    user = UserProfile.objects.get(user__username=username)
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN

    course = Course.objects.get(pk=course_pk)
    resit_course = Course.objects.get(pk=resit_course_id)

    try:
        course.resit_course = resit_course
        course.save()
    except:
        print("Couldn't assign resit course")
    
    
@shared_task
def task_update_assignment_deadlines(username, assignment_pks, unlock_time_string, deadline_time_string, lock_time_string, only_visible_to_overrides):
    for assignment_pk in assignment_pks:
        task_update_assignment_deadline(username, assignment_pk, unlock_time_string, deadline_time_string, lock_time_string, only_visible_to_overrides)
    return "Done"

@shared_task
def task_update_assignment_deadline(username, assignment_id, unlock_time_string, deadline_time_string, lock_time_string, only_visible_to_overrides):
        
    user = UserProfile.objects.get(user__username=username)
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN

    canvas = Canvas(API_URL, API_TOKEN)
    
    assignment = Assignment.objects.get(pk=assignment_id)

    canvas_course = canvas.get_course(assignment.course.course_id)
    canvas_assignment = canvas_course.get_assignment(assignment.assignment_id)

    try:    
        canvas_assignment.edit(assignment={
            "due_at": deadline_time_string,
            "unlock_at": unlock_time_string,
            "lock_at": lock_time_string
            })
    except:
        pass

    if only_visible_to_overrides:
        canvas_assignment.edit(
            assignment = {
                "only_visible_to_overrides": only_visible_to_overrides
            }
        )

    
    assignment.due_at = json_to_datetime(deadline_time_string)
    assignment.unlock_at = json_to_datetime(unlock_time_string)
    assignment.lock_at = json_to_datetime(lock_time_string)
    assignment.save()

    assignment.save()
    print("assignment saved!")

@shared_task
def task_assign_markers(username, data):
    for row in data:
        assignment = Assignment.objects.get(assignment_id = row["assignment_id"])
        submissions = Submission.objects.filter(assignment=assignment)
        print("submissions:", len(submissions))
        
        try:
            submission = Submission.objects.get(student__canvas_id = int(row["student_id"]), assignment=assignment)
            submission.marker = row["marker"]
            submission.marker_email = row["marker_email"]
            submission.save()

        except:
            continue

    return "Markers Assigned!"
    

@shared_task
def task_apply_zero_scores(username, submission_pks):
    for submission_pk in submission_pks:
        task_apply_zero_score(username, submission_pk)
    return "Done"

def task_apply_zero_score(username, submission_pk):
    user = UserProfile.objects.get(user__username=username)
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN

    submission = Submission.objects.get(pk=submission_pk)

    canvas = Canvas(API_URL, API_TOKEN)

    try:
        course = canvas.get_course(submission.course.course_id)
        assignment = course.get_assignment(submission.assignment.assignment_id)

        canvas_submission = assignment.get_submission(user=int(submission.student.canvas_id))
        
        if canvas_submission.entered_score !=0 and canvas_submission.seconds_late >= 3600*24*5:
            print("Applying zero score")

            text_comment= 'This submission has been awarded a score of 0 because it is more than 5 days late. If you believe this is incorrect please \n contact SLS-Assessment@liverpool.ac.uk. The original score for this submission was {}'.format(canvas_submission.entered_score) 
            canvas_submission.edit(submission={'posted_grade':0},comment={'text_comment':text_comment})
            update_submissions(username, [submission_pk])

    except:
        print("Couldn't apply zero scores")

@shared_task
def task_apply_cat_bs(username, submission_pks):
    for submission_pk in submission_pks:
        task_apply_cat_b(username, submission_pk)
    return "Done"

def task_apply_cat_b(username, submission_pk):
    user = UserProfile.objects.get(user__username=username)
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN

    submission = Submission.objects.get(pk=submission_pk)

    canvas = Canvas(API_URL, API_TOKEN)

    try:
        course = canvas.get_course(submission.course.course_id)
        assignment = course.get_assignment(submission.assignment.assignment_id)
        print("course_code", course.course_code)

        if course.course_code[4] == "7":
            cap = 50
            print("capping at 50")
        else:
            cap = 40

        canvas_submission = assignment.get_submission(user=int(submission.student.canvas_id))
        
        if canvas_submission.entered_score !=0:
            print("Applying Cat B Cap")

            text_comment= 'The Academic Integrity Committee has found that a Category B error has been made. In line with the Code of Practice on Assessment your mark has been capped at {0}%. The original score for this submission was {1}. If you have any queries please contact sls-integrity@liverpool.ac.uk'.format(str(cap), canvas_submission.entered_score) 
            canvas_submission.edit(submission={'posted_grade':cap},comment={'text_comment':text_comment})
            update_submissions(username, [submission_pk])
    except:
        print("Couldn't apply cat_b")

@shared_task
def task_apply_cat_cs(username, submission_pks):
    for submission_pk in submission_pks:
        task_apply_cat_c(username, submission_pk)
    return "Done"

def task_apply_cat_c(username, submission_pk):
    user = UserProfile.objects.get(user__username=username)
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN

    submission = Submission.objects.get(pk=submission_pk)

    canvas = Canvas(API_URL, API_TOKEN)

    try:
        course = canvas.get_course(submission.course.course_id)
        assignment = course.get_assignment(submission.assignment.assignment_id)
        print("course_code", course.course_code)

        cap = 0

        canvas_submission = assignment.get_submission(user=int(submission.student.canvas_id))
        
        if canvas_submission.entered_score !=0:
            print("Applying Cat C Cap")

            text_comment= 'The Academic Integrity Committee has found that a Category C error has been made. In line with the Code of Practice on Assessment your mark has been capped at {0}%. The original score for this submission was {1}. If you have any queries please contact sls-integrity@liverpool.ac.uk'.format(str(cap), canvas_submission.entered_score) 
            canvas_submission.edit(submission={'posted_grade':cap},comment={'text_comment':text_comment})
            update_submissions(username, [submission_pk])
    except:
        print("Couldn't apply cat_c")

@shared_task
def task_award_five_min_extensions(username, submission_pks):
    for submission_pk in submission_pks:
        task_award_five_min_extension(username, submission_pk)
    return "Done"

def task_award_five_min_extension(username, submission_pk):
    user = UserProfile.objects.get(user__username=username)
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN

    submission = Submission.objects.get(pk=submission_pk)

    canvas = Canvas(API_URL, API_TOKEN)

    try:
        course = canvas.get_course(submission.course.course_id)
        assignment = course.get_assignment(submission.assignment.assignment_id)
        user = canvas.get_user(submission.student.canvas_id)
        print(user.__dict__)

        # Check for existing overrides/extensions
        overrides = [x for x in assignment.get_overrides() if user.id in x.__dict__.get("student_ids", [])]

        if len(overrides) > 0:
            print("override exists")
            print(overrides[0].__dict__)
            override = overrides[0]
            override.edit(
                assignment_override={"due_at": override.due_at_date + timedelta(minutes=5)}
            )
            print("override updated")
            update_submissions(username, [submission_pk])
            print("submission updated")
        else:
            print("no override exists")


            assignment.create_override(assignment_override={"student_ids": [user.id], "due_at": submission.assignment.due_at + timedelta(minutes=5)})
            print("override created")


    except:
        print("Couldn't award five minute extensions")

@shared_task
def task_get_all_enrollments(username):
    user = UserProfile.objects.get(user__username=username)
    course_pks = [x.course_id for x in Course.objects.filter(course_department=user.department)]
    task_get_enrollments_by_courses(username, course_pks)

@shared_task
def task_get_enrollments_by_courses(username, course_ids):
    for course_id in course_ids:
        task_get_enrollments_by_course(username, course_id)

@shared_task
def task_get_enrollments_by_course(username, course_id):
    user = UserProfile.objects.get(user__username=username)
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN

    canvas = Canvas(API_URL, API_TOKEN)

    course = canvas.get_course(course_id)

    enrollments = [x for x in course.get_enrollments(include=["user"]) if x.type=="StudentEnrollment"]

    for enrollment in enrollments:

        # Check enrollment exists
        try:
            enrollments = Enrollment.objects.filter(canvas_id=enrollment.id, course__course_id=course_id)
            for e in enrollments:
                e.delete()
        except:
            print("no enrollment")


        # Get engagement record
        try:
            for item in engagement_data:
                if item.id == enrollment.user_id:
                    page_views = item.page_views
                    participations = item.participations
        except:
            page_views = None
            participations = None
            print("engagement not updated")

        # Get average assignment score
        submissions = Submission.objects.filter(student__canvas_id=enrollment.user_id, 
                                                course__course_id=course_id)
        print("user_id:", enrollment.user_id)
        try:
            for submission in submissions:
                print("submission:", submission)

            scores = [x.score for x in submissions if x.score != None]
            average_score = sum(scores)/len(scores)

        except:
            print("no submissions")
            average_score = None

        # Create enrollment
        #try:
        enrollment = Enrollment(
            name=enrollment.user["sortable_name"],
            canvas_course_id=course_id,
            canvas_id=enrollment.id,
            canvas_user_id = enrollment.user_id,
            login_id=enrollment.user["login_id"],
            sis_user_id=enrollment.user["sis_user_id"],
            course = Course.objects.get(course_id=course_id),
            page_views = page_views,
            participations = participations,
            average_assignment_score = average_score
        ).save()
        #except:
            #print("Couldn't add enrollment")
            #continue

@shared_task
def task_copy_to_resit_course(username, assignment_id):
    user = UserProfile.objects.get(user__username=username)
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN

    # Create a canvas handle
    canvas = Canvas(API_URL, API_TOKEN)

    # Get the assignment object from Lens
    assignment = Assignment.objects.get(assignment_id=assignment_id)

    # Check if resit course has been assigned to course
    if Course.objects.get(course_id=assignment.course.course_id).resit_course is None:
        return None

    # Get course object from Canvas
    course = canvas.get_course(assignment.course.course_id)

    # Get the original assignment object from Canvas
    old_assignment = canvas.get_course(course.id).get_assignment(assignment_id)

    resit_course = canvas.get_course(Course.objects.get(course_id=assignment.course.course_id).resit_course.course_id)

    resit_course_assignments = [x.name for x in resit_course.get_assignments()]

    consolidated_title = consolidate_title(assignment.assignment_name)

    if "RESIT " + consolidated_title not in resit_course_assignments:

        resit_course.create_content_migration(
            migration_type="course_copy_importer",
            settings={"source_course_id": str(course.id)},
            select={"assignments": [assignment_id]}
        )

        start = time.time()

        """
        Create a while loop that runs for 20 minutes. If the migration is complete, break the loop. If not, wait 30 seconds and try again.
        """
        while True:
            try:
                new_assignment = [x for x in resit_course.get_assignments() if x.name == old_assignment.name][0]
                compare_assignments = [x.name for x in resit_course.get_assignments()]
                if "RESIT " + consolidated_title in compare_assignments:
                    new_assignment.delete()
                    print("Assignment already exists in resit course")
                print("Old Assignment Name", old_assignment.name, "Assignment Lens Name", assignment.assignment_name)
                new_assignment.edit(
                    assignment={"name": "RESIT " + consolidated_title,
                                "unlock_at": "",
                                "lock_at": "",
                                "due_at": "",
                                "description": "",
                                "only_visible_to_overrides": True},
                )
            except:
                print("no dice")

                if time.time() - start > 300:
                    break
                else:
                    time.sleep(30)
                    continue

            break

        # Remove duplicate assignments
        delete_duplicate_assignments(resit_course)
        return None
    else:
        delete_duplicate_assignments(resit_course)
        return "Assignment already exists in resit course"

def consolidate_title(title):
  if "surname" in title.lower():
    new_title = title.split(".")
    if len(new_title[1])==1:
      label = ".".join(new_title[:2])
      end = new_title[2][1:]
      new_title = label+end
    new_title = new_title.upper()
    if "STUDENT" in new_title:
      new_title = new_title.split("STUDENT")[0]
    if "SURNAME" in new_title:
      new_title = new_title.split("SURNAME")[0]
    if new_title[-2:-1] == "-":
      new_title = new_title[:-2]
    return new_title.strip()
  else:
    return title

@shared_task
def task_make_only_visible_to_overrides(username, assignment_id):
    user = UserProfile.objects.get(user__username=username)
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN

    # Create a canvas handle
    canvas = Canvas(API_URL, API_TOKEN)

    # Get the assignment object from Lens
    assignment = Assignment.objects.get(assignment_id=assignment_id)

    # Get course object from Canvas
    course = canvas.get_course(assignment.course.course_id)

    # Get the original assignment object from Canvas
    old_assignment = canvas.get_course(course.id).get_assignment(assignment_id)

    old_assignment.edit(
        assignment={"only_visible_to_overrides": True}
    )

    return "Done"

def delete_duplicate_assignments(course):
    # Remove duplicate assignments
    all_assignments = [x for x in course.get_assignments()]

    #for assignment in all_assignments:
        #if assignment.name != consolidate_title(assignment.name):
            #assignment.edit(assignment={"name": consolidate_title(assignment.name)})

    assignment_names = [x.name for x in all_assignments]

   

    for assignment_name in assignment_names:
        if assignment_names.count(assignment_name) > 1:

            assignments_to_delete = [x for x in all_assignments if x.name == assignment_name][1:]

            for assignment_to_delete in assignments_to_delete:
                try:
                    assignment_to_delete.delete()
                except:
                    continue

@shared_task
def task_create_assignment_summary(username, course_id):
    user = UserProfile.objects.get(user__username=username)
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN

    # Create a canvas handle
    canvas = Canvas(API_URL, API_TOKEN)

    # Get course object from Canvas
    course = canvas.get_course(int(course_id))

    # Get all assignments
    assignments = sorted([x for x in course.get_assignments(include=["overrides"])], key=lambda x: x.name)

    course_code_set = sorted(list(set([find_substring(x.name) for x in assignments if find_substring(x.name) != None])))

    page_html = ""

    for course_code in course_code_set:
        page_html += "<h2>{}</h2>".format(course_code)
        page_html += '''<style type="text/css">
.tg  {border-collapse:collapse;border-spacing:0;}
.tg td{border-color:black;border-style:solid;border-width:1px;font-family:Arial, sans-serif;font-size:14px;
  overflow:hidden;padding:10px 5px;word-break:normal;}
.tg th{border-color:black;border-style:solid;border-width:1px;font-family:Arial, sans-serif;font-size:14px;
  font-weight:normal;overflow:hidden;padding:10px 5px;word-break:normal;}
.tg .tg-0pky{border-color:inherit;text-align:left;vertical-align:top}
.tg-title{width:50%}
</style>
<table class="tg" style="width:75%">
<thead>
      <tr>
        <th>Assignment Name</th>
        <th>Resitting Students</th>
        <th>Unlock At</th>
        <th>Deadline At</th>
        <th>Lock At</th>
        <th>Edit</th>
        <th>SpeedGrader</th>
      </tr>
    </thead>
<tbody>'''
        for assignment in assignments:
            if find_substring(assignment.name) == course_code:
                # create a truncated name variable that is exactly 128 characters long
                # If it's length is less than 238 then make it up with spaces
                if len(assignment.name) > 128:
                    truncated_name = assignment.name[:128]+"..."
                else:
                    truncated_name = assignment.name + " "*(125-len(assignment.name))
                

                print(assignment.name)

                resitting_students = 0
                if len(assignment.overrides) > 0:
                    for override in assignment.overrides:
                        resitting_students += len(override.student_ids)
                
                assignment_due_at = assignment.due_at

                # make assignment_due_at time 12:00
                try:
                    assignment_due_at = assignment_due_at.replace(hour=11, minute=0, second=0, microsecond=0)
                except:
                    pass
                        
                unlock_at = iso_to_human(assignment.unlock_at)
                due_at = iso_to_human(assignment_due_at)
                lock_at = iso_to_human(assignment.lock_at)
                    

                speed_grader_url = API_URL+"/courses/{}/gradebook/speed_grader?assignment_id={}".format(course_id, assignment.id)
                page_html += '<tr>'
                page_html += '<td class="tg-0pky" style="width:40%">{}</td>'.format(truncated_name)
                page_html += '<td class="tg-0pky" style="width:10%">{}</td>'.format(resitting_students)
                page_html += '<td class="tg-0pky" style="width:10%">{}</td>'.format(unlock_at)
                page_html += '<td class="tg-0pky" style="width:10%">{}</td>'.format(due_at)
                page_html += '<td class="tg-0pky" style="width:10%">{}</td>'.format(lock_at)
                page_html += '<td class="tg-0pky" style="width:10%"><a href="{}/edit">Edit</a></td>'.format(assignment.html_url)
                page_html += '<td class="tg-0pky" style="width:10%"><a href="{}">SpeedGrader</a></td>'.format(speed_grader_url)
                page_html += '</tr>'
        page_html += "</tbody></table><br>"

    # If page exists, delete it
    try:
        course.get_page("assignment-directory").delete()
    except:
        pass
            
    # Create page
    course.create_page(
        wiki_page={"title": "Assignment Directory",
                    "body": page_html,
                    "published": False}
    )

def find_substring(string):
    pattern = r'[A-Z]{4}\d{3}'
    matches = re.findall(pattern, string)
    try:
      return matches[0]
    except:
      return None
    
@shared_task
def task_enroll_teachers_on_resit_course(username, course_id):
    user = UserProfile.objects.get(user__username=username)
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN
    canvas = Canvas(API_URL, API_TOKEN)

    course = canvas.get_course(course_id)

    resit_course_id = Course.objects.get(course_id=course_id).resit_course.course_id

    try:
        resit_course = canvas.get_course(resit_course_id)
    except:
        return None

    teachers = [x for x in course.get_enrollments() if x.type=="TeacherEnrollment"]

    for teacher in teachers:
        try:
            resit_course.enroll_user(teacher.user_id, enrollment_type="TeacherEnrollment", enrollment={"enrollment_type": "TeacherEnrollment",
                                                                  "enrollment_state": "active"})
        except:
            print("Couldn't enroll teacher")

def iso_to_datetime(dt):
    try:    
        return datetime.strptime(dt, "%Y-%m-%dT%H:%M:%SZ")
    except:
        return None

def iso_to_human(dt):
    try:
        new_dt = iso_to_datetime(dt) + timedelta(hours=1)
        return new_dt.strftime("%d/%m/%Y %H:%M")
    except:
        return None
    
@shared_task
def task_assign_to_next_term(username, assignment_id):
    user = UserProfile.objects.get(user__username=username)
    assignment = Assignment.objects.get(assignment_id=assignment_id)

    if assignment.rollover_to_course is not None:
        return f"{assignment.assignment_name}: Assignment already assigned to next term"
    
    try:
        course = assignment.course
        term = int(find_first_match(term_pattern, course.course_code))
        course_code = find_first_match(course_pattern, assignment.assignment_name)
        next_term = term + 101
        next_course_string = course_code + '-' + str(next_term)
        next_course = Course.objects.get(course_code=next_course_string)
        assignment.rollover_to_course = next_course
        assignment.save()
        return f"{assignment.assignment_name}: Assignment assigned to next term"
    except:
        return f"{assignment.assignment_name}: Couldn't assign assignment to next term"
  

    return "Assignment updated"

@shared_task
def task_copy_to_next_term_course(username, assignment_id):
    print("task_copy_to_next_term_course")

    user = UserProfile.objects.get(user__username=username)
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN

    # Create a canvas handle
    canvas = Canvas(API_URL, API_TOKEN)

    # Get the assignment object from Lens
    assignment = Assignment.objects.get(assignment_id=assignment_id)    

    term = int(find_first_match(term_pattern, assignment.course.course_code))
    next_term = term + 101

    course_code = find_first_match(course_pattern, assignment.assignment_name)
    course_code = course_code + '-' + str(term)
    next_course_code = course_code.replace(str(term), str(next_term))

    print("next_term_course:", next_course_code)

    # Get course object from Canvas
    course = canvas.get_course(assignment.course.course_id)

    # Get the original assignment object from Canvas
    old_assignment = canvas.get_course(course.id).get_assignment(assignment_id)

    next_course = canvas.get_course(next_course_code, use_sis_id=True)

    next_course_assignments = [x.name for x in next_course.get_assignments()]

    # remove "RESIT " from assignment name
    new_title = assignment.assignment_name.replace("RESIT", "").strip()

    if new_title not in next_course_assignments:



        next_course.create_content_migration(
            migration_type="course_copy_importer",
            settings={"source_course_id": str(course.id)},
            select={"assignments": [assignment_id]}
        )
  

        start = time.time()

        """
        Create a while loop that runs for 20 minutes. If the migration is complete, break the loop. If not, wait 30 seconds and try again.
        """
        while True:
            try:
                new_assignment = [x for x in next_course.get_assignments() if x.name == old_assignment.name][0]
                compare_assignments = [x.name for x in next_course.get_assignments()]
                if new_title in compare_assignments:
                    new_assignment.delete()
                    print("Assignment already exists in resit course")
                print("Old Assignment Name", old_assignment.name, "Assignment Lens Name", assignment.assignment_name)

                new_assignment.edit(
                    assignment={"name": new_title,
                                "unlock_at": "",
                                "lock_at": "",
                                "due_at": "",
                                "description": "",
                                "only_visible_to_overrides": True,
                                "published": False,
                                "anonymous_grading": True}
                                #"assignment_group_id": assignment_group.id},
                )

                # get assignment group
                # assignment_group = get_assignment_group(next_course, new_assignment, API_URL, API_TOKEN)

            except:
                print("no dice")

                if time.time() - start > 300:
                    break
                else:
                    time.sleep(30)
                    continue

            break

        # Remove duplicate assignments
        delete_duplicate_assignments(next_course)
        return None
    else:
        delete_duplicate_assignments(next_course)
        return "Assignment already exists in resit course"
    
@shared_task   
def task_duplicate_for_resit(username, assignment_id):
    user = UserProfile.objects.get(user__username=username)
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN

    canvas = Canvas(API_URL, API_TOKEN)

    assignment = Assignment.objects.get(assignment_id=assignment_id)
    course_id = assignment.course.course_id

    headers = {'Authorization': 'Bearer {}'.format(API_TOKEN)}
    url = '{}/api/v1/courses/{}/assignments/{}/duplicate'.format(API_URL, course_id, assignment_id)

    r = requests.post(url, headers=headers)

    if r.status_code == 200:

        a = canvas.get_course(course_id).get_assignment(r.json()["id"])
        a.edit(assignment={"name": "RESIT " + assignment.assignment_name.replace("Copy", ""),
                        "unlock_at": "",
                        "lock_at": "",
                        "due_at": "",
                        "description": "",
                        "published": False,
                        "only_visible_to_overrides": True})
        
        return "Assignment duplicated for RESIT"
    else:
        return "Couldn't duplicated for RESIT"

@shared_task
def task_organise_assignments(username, course_id):
    print("task_organise_assignments")

    user = UserProfile.objects.get(user__username=username)
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN
    canvas = Canvas(API_URL, API_TOKEN)
    print("course_id:", course_id)
    course = canvas.get_course(course_id)

    # Get all assignments
    assignments = [x for x in course.get_assignments()]

    # order assignments by name
    assignments = sorted(assignments, key=lambda x: x.name)

    # Organise assignments into groups
    for assignment in assignments:
        # Extract weight
        try:
            weight = find_first_match(weight_pattern, assignment.name)

            # get integer from string using regex
            weight = int(re.findall(r'\d+', weight)[0])

            print(assignment, weight)
        except:
            weight = None

        # Extract assignment label
        #try:
        assignment_label = find_first_match(assignment_pattern, assignment.name)[:9]
            
        # Check assignment group
        group = get_assignment_group(course, assignment_label, weight, API_URL, API_TOKEN)

        # Move assignment to group
        assignment.edit(assignment={"assignment_group_id": group.id})

        print("Assignment {} moved to group {}".format(assignment.name, group.name))

        #except:
            #print("Couldn't extract assignment label")
            #continue

        course.update(
            course={"apply_assignment_group_weights": True}
        )

    return "Assignments organised."

        
def get_assignment_group(course, assignment_label, weight, API_URL, API_TOKEN):

    # Check if group exists
    try:
        assignment_groups = [x for x in course.get_assignment_groups()]
        group = [x for x in assignment_groups if x.name == assignment_label][0]
        return group
    except:
        # Create group

        headers = {'Authorization': 'Bearer {}'.format(API_TOKEN)}
        url = '{}/api/v1/courses/{}/assignment_groups'.format(API_URL, course.id)

        data = {
        'name': assignment_label[:9],
        'group_weight': weight,
        }

        r = requests.post(url, data=data, headers=headers)
        
        if r.status_code == 200:
            group_data = r.json()
            group = course.get_assignment_group(group_data["id"])
            return group
        
@shared_task
def task_hide_totals(username, course_id):
    print("task_hide_totals")

    user = UserProfile.objects.get(user__username=username)
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN
    canvas = Canvas(API_URL, API_TOKEN)

    headers = {'Authorization': 'Bearer {}'.format(API_TOKEN)}
    url = '{}/api/v1/courses/{}/settings'.format(API_URL, course_id)

    data = {
        'hide_final_grades':True
    }

    r = requests.put(url, data=data, headers=headers)

    if r.status_code == 200:
        return "Totals hidden"
    else:
        return "Couldn't hide totals"
    
@shared_task
def task_turn_on_late_policy(username, course_id):

    user = UserProfile.objects.get(user__username=username)
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN

    course = Course.objects.get(course_id=course_id)

    course_pattern = r'[A-Z]{4}\d{3}'

    # Get first 3 digit number in course.name
    course_code = find_first_match(course_pattern, course.course_code)
    
    late_submission_minimum_percent = '40'

    print("course_code:", course_code, type(course_code))

    # If course_code is string
    if type(course_code) == str:
        if course_code[4] == "7":
            print("capping at 50")
            late_submission_minimum_percent = '50'      
            

    url = API_URL + "/api/v1/courses/{}/late_policy".format(course_id)
    payload = {
        'late_policy[late_submission_deduction_enabled]': 'true',
        'late_policy[late_submission_deduction]': '5',
        'late_policy[late_submission_interval]': 'day',
        'late_policy[late_submission_minimum_percent_enabled]': 'true',
        'late_policy[late_submission_minimum_percent]': late_submission_minimum_percent,  
    }

    headers = {
        'Authorization': 'Bearer ' + API_TOKEN,
    }
    response = requests.patch(
        url = url,
        data = payload,
        headers = headers,
    )
    return "Done"





