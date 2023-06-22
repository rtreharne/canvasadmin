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

logger = get_task_logger(__name__)

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
            assignment.average_score = round(average_score, 1)
            assignment.save()
        except:
            continue

    app_canvas_mapp = {
        #"assignment_name": "name",
        "unlock_at": "unlock_at",
        "lock_at": "lock_at",
        #"due_at": "due_at",
        "needs_grading_count": "needs_grading_count",
        "published": "published",
        "anonymous_grading": "anonymous_grading",
        "type": "submission_types",
        "has_overrides": "has_overrides",
    }

    for a in assignments:
        # get canvas assignment
        
        try:
            canvas_assignment = canvas.get_course(a.course.course_id).get_assignment(a.assignment_id)
            assignment_found = True
        except:
            assignment_found = False

        if assignment_found:
            for key, value in app_canvas_mapp.items(): 
                    
                if key == "due_at":
                    print("updating due_at")
                    if canvas_assignment.has_overrides:
                        print("has overrides")
                        assignment = [x for x in canvas.get_course(a.course.course_id).get_assignments(include=["all_dates"]) if x.id == a.assignment_id][0]
                        dates = assignment.all_dates
                        for date in dates:
                            print(date.keys())
                            if "base" in date.keys():
                                datetime = is_datetime(date["due_at"])
                else:

                    datetime = is_datetime(canvas_assignment.__dict__.get(key, None))

                

                    
                if datetime:
                    if len(str(a.__dict__[key])) <1:
                        pass
                    else:
                        #try:
                            #dt_flag=True
                            #datetime != a.__dict__[key].replace(tzinfo=None)
                        #except:
                            #dt_flag=False

                        
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
                        try:    
                            a.pc_ungraded = float("{:.2f}".format(100*a.graded/(a.graded+a.ungraded)))
                        except:
                            a.pc_ungraded = 0
                        a.save()
                else:
                    if canvas_assignment.__dict__[value] != a.__dict__[key]:
                        if key == "needs_grading_count":
                            summary = get_submission_summary(API_URL, API_TOKEN, course_id=a.course.course_id, assignment_id=a.assignment_id)

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

        submissions = [x for x in a.get_submissions(include=["assignment", "user", "submission_comments", "full_rubric_assessment"])]

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

            if len(new_submission) == 0:

                if sub.submitted_at != None:

                    # look for category concerns
                    concerns = {
                        "category a": "A",
                        "category b": "B",
                        "category c": "C, D or E"
                    }
                    
                    integrity_flag = None
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
                    except:
                        print("submission not added")


@shared_task()
def update_submissions(username, submission_ids):
    user = UserProfile.objects.get(user__username=username)
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN
    canvas = Canvas(API_URL, API_TOKEN)

    submissions = Submission.objects.filter(submission_id__in=submission_ids)

    app_canvas_mapp = {
        "score": "score",
        "seconds_late": "seconds_late",
    }

    

    for i, sub in enumerate(submissions):

        # Does student have sis_user_id?
        

        try:
            canvas_submission = canvas.get_course(sub.assignment.course.course_id).get_assignment(sub.assignment.assignment_id).get_submission(sub.student.canvas_id, include=["user", "submission_comments", "full_rubric_assignment"])
        except:
            print("couldn't get canvas submission")
            continue
        

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

        for key, value in app_canvas_mapp.items():

            if sub.__dict__[key] != canvas_submission.__dict__[value]:

                

                SubmissionLog(
                            student=sub.student,
                            submission=sub.assignment,
                            course=sub.assignment.course.course_code,
                            request="UPDATE",
                            field=key,
                            from_value=str(sub.__dict__[key]),
                            to_value=str(canvas_submission.__dict__[value]),
                            department=user.department
                            ).save()
    
                setattr(sub, key, canvas_submission.__dict__[value])
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
def task_update_assignment_deadlines(username, assignment_pks, time_string):
    for assignment_pk in assignment_pks:
        task_update_assignment_deadline(username, assignment_pk, time_string)
    return "Done"

@shared_task
def task_update_assignment_deadline(username, assignment_id, time_string):
        
    user = UserProfile.objects.get(user__username=username)
    API_URL = user.department.CANVAS_API_URL
    API_TOKEN = user.department.CANVAS_API_TOKEN

    canvas = Canvas(API_URL, API_TOKEN)
    
    assignment = Assignment.objects.get(pk=assignment_id)

    canvas_course = canvas.get_course(assignment.course.course_id)
    canvas_assignment = canvas_course.get_assignment(assignment.assignment_id)
    try:    
        canvas_assignment.edit(assignment={"due_at": time_string})
    except:
        canvas_assignment.edit(assignment={"due_at": time_string, "lock_at": time_string})

    
    assignment.due_at = json_to_datetime(time_string)

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

        # Check for existing overrides/extensions
        overrides = [x for x in assignment.get_overrides() if user in x.__dict__.get("student_ids", [])]

        if len(overrides) > 0:
            print("override exists")
        else:
            print("no override exists")


            #assignment.create_override(assignment_override={"student_ids": [user.id], "due_at": submission.assignment.due_at + timedelta(minutes=5)})
            #print("override created")


    except:
        print("Couldn't award five minute extensions")

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

    # Get engagement data
    engagement_data = [x for x in course.get_course_level_student_summary_data()]

    print(engagement_data)

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

def delete_duplicate_assignments(course):
    # Remove duplicate assignments
        all_assignments = [x for x in course.get_assignments()]
        for assignment in all_assignments:
            if assignment.name != consolidate_title(assignment.title):
                assignment.edit(assignment={"name": consolidate_title(assignment.name)})

        assignment_names = [x.name for x in all_assignments]

        for assignment_name in assignment_names:
            if assignment_names.count(assignment_name) > 1:

                assignments_to_delete = [x for x in all_assignments if x.name == assignment_name][1:]
                for assignment_to_delete in assignments_to_delete:
                    try:
                        assignment_to_delete.delete()
                    except:
                        continue







    





