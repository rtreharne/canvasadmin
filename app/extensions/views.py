from django.shortcuts import render
from django.http import HttpResponseRedirect
from .forms import StudentIdForm, CourseForm, AssignmentForm
from django.urls import reverse
from core.models import Assignment, Student, Course
from extensions.models import Extension
import datetime

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
            return HttpResponseRedirect('/forms/{}/'.format(student_id))
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
            return HttpResponseRedirect('/forms/{}/{}/'.format(student_id, course_canvas_id))
    else:
        form = CourseForm(student_id=student_id)

    return render(request, 'extensions/extensions_course.html', {'form': form})

def assignment(request, student_id, course_canvas_id):
    """
    Render a page with an AssignmentForm for the course.
    """
    if request.method == 'POST':
        form = AssignmentForm(request.POST, course_canvas_id=course_canvas_id)
        if form.is_valid():

            print(form.cleaned_data)

            student = Student.objects.get(sis_user_id__contains=student_id)
            course = Course.objects.get(course_id=course_canvas_id)


            assignment = Assignment.objects.get(assignment_id=form.cleaned_data['assignment'])
            extension_type = form.cleaned_data['extension_type']
            extension = int(form.cleaned_data['extension'])
            reason = form.cleaned_data['reason']
            

            assignment_due_at = assignment.due_at
            extension_deadline = assignment_due_at + datetime.timedelta(weeks=extension)

            # Create and save extension object
            extension = Extension(
                unique_id = student_id,
                student = student,
                extension_type = extension_type,
                course = course,
                assignment = assignment,
                extension_deadline = extension_deadline,
                original_deadline = assignment.due_at,
                reason = reason,
                apply_to_subcomponents = False
                ).save()          


            return HttpResponseRedirect(reverse('extensions:success'))
    else:
        form = AssignmentForm(course_canvas_id=course_canvas_id)

    return render(request, 'extensions/extensions_assignment.html', {'form': form})

    

def success(request):
    return render(request, 'extensions/extensions_success.html')
