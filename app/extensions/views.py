from django.shortcuts import render
from django.http import HttpResponseRedirect
from .forms import StudentIdForm, CourseForm, AssignmentForm
from django.urls import reverse
from core.models import Assignment, Student, Course, Submission
from extensions.models import Extension
import datetime
from .tasks import send_receipt
from .models import Extension, Date
from canvasapi import Canvas


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

    return render(request, 'extensions/extensions_index.html', {'form': form})

def course(request, student_id):
    """
    Render a page with a CourseForm for the student.
    """
    if request.method == 'POST':
        form = CourseForm(request.POST, student_id=student_id)
        if form.is_valid():
            course_canvas_id = form.cleaned_data['course']
            return HttpResponseRedirect('/elp/{}/{}/'.format(student_id, course_canvas_id))
    else:
        form = CourseForm(student_id=student_id)

    return render(request, 'extensions/extensions_course.html', {'form': form})

def assignment(request, student_id, course_canvas_id):
    """
    Render a page with an AssignmentForm for the course.
    """
    if request.method == 'POST':
        form = AssignmentForm(request.POST, student_id=student_id, course_canvas_id=course_canvas_id)
        if form.is_valid():

            print(form.cleaned_data)

            student = Student.objects.get(sis_user_id__contains=student_id)
            course = Course.objects.get(course_id=course_canvas_id)


            assignment = Assignment.objects.get(assignment_id=form.cleaned_data['assignment'])
            reason = form.cleaned_data['reason']
            

            # Check Lens for submission
            # If DoesNotExist, then return error message
            # If Exists, then get the submission object
            try:
                submission = Submission.objects.get(student=student, assignment=assignment)
            except Submission.DoesNotExist:
                error_message = ''
                error_message += '<p class="error">You cannot apply for an ELP until you have made a submission via Canvas.</p>'
                error_message += '<p>If you have submitted then, apologies. Try again in a few minutes.</p>'
      
                return render(request, 'extensions/extensions_assignment.html', {'form': form,
                                                                                  'error_message': error_message})

            # Create and save extension object
            extension = Extension(
                unique_id = student_id,
                student = student,
                course = course,
                assignment = assignment,
                extension_deadline = submission.submitted_at + datetime.timedelta(hours=1, minutes=5),
                original_deadline = assignment.due_at,
                reason = reason,
                apply_to_subcomponents = False,
                ).save()
            
            print(extension)

            # Send email to student using Canvas conversation API
            current_host = request.get_host()

            conversation = send_receipt(extension, current_host)

            if conversation:
                print("confirmation email sent")
            else:
                print("confirmation email not sent")

            return HttpResponseRedirect(reverse('extensions:success'))
    else:
        form = AssignmentForm(student_id=student_id, course_canvas_id=course_canvas_id)

    return render(request, 'extensions/extensions_assignment.html', {'form': form})

def confirmation(request, confirmation_id):
    """
    This view is used to confirm the extension.
    """

    # Get the extension object using the confirmation_id. If the extension does't exist then return an error message.
    try:
        extension = Extension.objects.get(confirmation_id=confirmation_id)
    except:
        return render(request, 'extensions/extensions_student_confirmation.html', {'confirmation_message': 'The ELP you are trying to confirm does not exist. Make a new application.'})
    
    if extension.confirmed:
        confirmation_message = "You have already confirmed your application for an ELP."
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
        count = Extension.objects.filter(student=extension.student, extension_deadline__lte=date.finish, extension_deadline__gte=date.start, approved=True).count()
        if count < 2:
            extension.approved = True
            extension.approved_on = datetime.datetime.now()
            extension.save()
            confirmation_message = "You have confirmed your application for an ELP. Your ELP has been automatically approved. You should see these changes reflected on Canvas shortly."
        else:
            confirmation_message = "You have confirmed your application for an ELP. You will be notified when your application has been approved."

    return render(request, 'extensions/extensions_student_confirmation.html', {'extension': extension,
                                                                       'confirmation_message': confirmation_message})

    

def success(request):
    return render(request, 'extensions/extensions_success.html')
