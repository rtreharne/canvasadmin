from django.shortcuts import render
from django.http import HttpResponseRedirect
from .forms import StudentIdForm, CourseForm, AssignmentForm
from django.urls import reverse
from core.models import Assignment, Student, Course, Submission
from extensions.models import Extension
import datetime
from .tasks import send_receipt, task_apply_override, send_approved
from .models import Extension, Date
from canvasapi import Canvas
from core.tasks import task_get_submission

# Create your views here.

def student_id(request):

    """
    Check form for valid data.
    If valid, redirect to success page.
    If invalid, render form again with error messages.
    """
    if request.method == 'POST':
        form = StudentIdForm(request.POST)
        if form.is_valid():
            student_id = form.cleaned_data['student_id']
            return HttpResponseRedirect('{}/'.format(student_id))
    else:
        form = StudentIdForm()

    # get current url
    root = list(filter(None, request.build_absolute_uri().split('/')))[-1]
    if root == 'elp':
        return render(request, 'extensions/elp_index.html', {'form': form})
    if root == 'extensions':
        return render(request, 'extensions/extensions_index.html', {'form': form})


def course(request, student_id):
    """
    Render a page with a CourseForm for the student.
    """
    root = list(filter(None, request.build_absolute_uri().split('/')))[-2]
    print(root)
    if request.method == 'POST':
        form = CourseForm(request.POST, student_id=student_id)
        if form.is_valid():
            course_canvas_id = form.cleaned_data['course']
            if root == 'elp':
                return HttpResponseRedirect('/elp/{}/{}/'.format(student_id, course_canvas_id))
            elif root == 'extensions':
                return HttpResponseRedirect('/extensions/{}/{}/'.format(student_id, course_canvas_id))
    else:
        form = CourseForm(student_id=student_id)

    if root == 'elp':
        return render(request, 'extensions/elp_course.html', {'form': form})
    elif root == 'extensions':   
        return render(request, 'extensions/extensions_course.html', {'form': form})

def assignment(request, student_id, course_canvas_id):
    """
    Render a page with an AssignmentForm for the course.
    """

    root = list(filter(None, request.build_absolute_uri().split('/')))[-3]
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES, student_id=student_id, course_canvas_id=course_canvas_id, root=root)

        # Handle any file uploads
        files = request.FILES.getlist('files')
        print(files)
        f = None
        if files:
            for f in files:
                extension = f.name.split(".")[-1]
                print(extension)
                if extension not in ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'zip']:
                    error_message = ''
                    error_message += '<p class="error">You have uploaded a file with an invalid extension. Please upload a file with one of the following extensions: pdf, doc, docx, jpg, jpeg, png.</p>'
                    return render(request, 'extensions/elp_assignment.html', {'form': form,
                                                                                'error_message': error_message})  
        if form.is_valid():

            print(form.cleaned_data)

            student = Student.objects.get(sis_user_id__contains=student_id)
            course = Course.objects.get(course_id=course_canvas_id)
            assignment = Assignment.objects.get(assignment_id=form.cleaned_data['assignment'])
            late_ignore = form.cleaned_data.get('late_ignore', False)
            reason = form.cleaned_data.get('reason', 'None')

            # Check if approved elp exists for assignment

            try:
                approved = Extension.objects.get(student=student, assignment=assignment, approved=True)
                error_message = ''
                if root == 'elp':
                    error_message += '<p class="error">You have already been granted an ELP for this assignment.</p>'
                    return render(request, 'extensions/elp_assignment.html', {'form': form,
                                                                                  'error_message': error_message})
                elif root == 'extensions':
                    error_message += '<p class="error">You have already been granted an extension for this assignment.</p>'
                    return render(request, 'extensions/extensions_assignment.html', {'form': form,
                                                                                    'error_message': error_message})
                
            except Extension.DoesNotExist:
                pass


                      
            
            if root == 'elp':
                # Check Lens for submission
                # If DoesNotExist, then return error message
                # If Exists, then get the submission object
                try:
                    submission = Submission.objects.get(student=student, assignment=assignment)
                    if late_ignore:
                        extension_deadline = submission.submitted_at + datetime.timedelta(minutes=5)
                        print("extension_deadline:", extension_deadline)
                        print("assignment.due_at:", assignment.due_at)
                        print("difference:", extension_deadline - assignment.due_at)
                        if submission.submitted_at - assignment.due_at > datetime.timedelta(minutes=5):
                            error_message = ''
                            error_message += '<p class="error">You ticked the box to say that you were less than 5 minutes late. However, the difference between the original deadline and the time you submitted is greater than 5 minutes. Please un-tick the "Less than 5 minutes late?" box and try again.</p>'
        
                            return render(request, 'extensions/elp_assignment.html', {'form': form,
                                                                                    'error_message': error_message})
                    else:
                        extension_deadline = submission.submitted_at + datetime.timedelta(minutes=5)
                except Submission.DoesNotExist:
                    error_message = ''
                    error_message += '<p class="error">You cannot apply for an ELP until you have submitted this assignment via Canvas.</p>'
                    error_message += '<p>If you have submitted recently then please wait a few minutes and try again.</p><p>If you are making an application more than 24 hours after submission and you are still seeing this message please contact <a href="mailto:SLSAssessment@liverpool.ac.uk">SLSAssessment@liverpool.ac.uk</a></p>'
                    task_get_submission.delay(request.user.username, assignment.assignment_id)

        
                    return render(request, 'extensions/elp_assignment.html', {'form': form,
                                                                                    'error_message': error_message})
            elif root == 'extensions':
                extension_deadline = assignment.due_at + datetime.timedelta(days=7, minutes=5)
            
            
            # Create and save extension object
            extension = Extension(
                unique_id = student_id,
                student = student,
                course = course,
                assignment = assignment,
                extension_deadline = extension_deadline,
                original_deadline = assignment.due_at,
                reason = reason,
                apply_to_subcomponents = False,
                late_ignore = late_ignore,
                files = f
                ).save()
            
            if root == 'extensions':
                extension.extension_type = 'EXTENSION'
                extension.save()

            # Send email to student using Canvas conversation API
            current_host = request.get_host()

            conversation = send_receipt(extension, current_host, root)

            if conversation:
                print("confirmation email sent")
            else:
                print("confirmation email not sent")

            if root == 'elp':
                return render(request, 'extensions/elp_success.html', {'form': form})
            elif root == 'extensions':
                return render(request, 'extensions/extensions_success.html', {'form': form})

            return HttpResponseRedirect(reverse('extensions:success'))
        
    else:
        form = AssignmentForm(student_id=student_id, course_canvas_id=course_canvas_id, root=root)

    if root == 'elp':
        return render(request, 'extensions/elp_assignment.html', {'form': form})
    elif root == 'extensions':
        return render(request, 'extensions/extensions_assignment.html', {'form': form})

def confirmation(request, confirmation_id):
    """
    This view is used to confirm the extension.
    """
    root = list(filter(None, request.build_absolute_uri().split('/')))[-3]
    print("ROOT", root)
    # Get the extension object using the confirmation_id. If the extension does't exist then return an error message.
    try:
        extension = Extension.objects.get(confirmation_id=confirmation_id)
    except:
        return render(request, 'extensions/elp_student_confirmation.html', {'confirmation_message': 'The extension/ELP you are trying to confirm does not exist. Make a new application.'})
    
    if extension.confirmed:
        confirmation_message = "You have already confirmed your application for this extension/ELP."
    else:
        extension.confirmed = True
        extension.save()

        # Get the current Date object based on the extension_deadeline.
        # Deadline must be within start and finish dates of the Date object.
        current_date = datetime.datetime.now().date()
        date = Date.objects.get(start__lte=extension.extension_deadline, finish__gte=extension.extension_deadline)
        print("Date:", date)

        # Count how many extensions have been confirmed for the current date for the student.
        # If the student has already had two or more extensions confirmed for the current date, then don't apply the extension.
        # If the student has had less than two extensions approved for the current date, then apply the extension.
        if root == 'elp':
            count = Extension.objects.filter(student=extension.student, extension_deadline__lte=date.finish, extension_deadline__gte=date.start, approved=True).exclude(late_ignore=True).count()
            print("Count:", count)
            if count < 2:
                extension.approved = True
                extension.approved_on = datetime.datetime.now()
                extension.save()
                confirmation_message = "You have confirmed your application for an ELP. Your ELP will be approved shortly. Following approval your assignment will no longer be subject to a late penatly."

                # Apply the extension to the assignment
                task_apply_override.delay(request.user.username, extension.id, root)
                current_host = request.get_host()

                conversation = send_approved(extension, root)
                # sync submission
            else:
                confirmation_message = "You have confirmed your application for an ELP. You will be notified of the outcome of your application."
        elif root == 'extensions':
            confirmation_message = "You have confirmed your application for an extension. You will be notified of the outcome of your application."
    if root == 'elp':
        return render(request, 'extensions/elp_student_confirmation.html', {'extension': extension,
                                                                       'confirmation_message': confirmation_message})
    elif root == 'extensions':
        return render(request, 'extensions/extensions_student_confirmation.html', {'extension': extension,
                                                                       'confirmation_message': confirmation_message})

    

def success(request):
    return render(request, 'extensions/extensions_success.html')
