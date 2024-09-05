from django import forms
from core.models import Student, Assignment
from enrollments.models import Enrollment
from extensions.models import Extension, Date
import datetime
from django.db.models import Q
from django.utils import timezone

class CsvImportForm(forms.Form):
    csv_file = forms.FileField()

class StudentIdForm(forms.Form):
    """
    This form should have a single field: student_id (int).
    It should be validated against the sis_user_id field in the Student model.
    The input integer should be 9 digits long and should be in the string of the sis_user_id field.
    """
    student_id = forms.IntegerField(label="Student ID")

    def clean_student_id(self):
        student_id = self.cleaned_data['student_id']
        #if len(str(student_id)) != 9:
            #raise forms.ValidationError("Student ID must be 9 digits long")
        return student_id
    
    def clean(self):

        cleaned_data = super(StudentIdForm, self).clean()
        student_id = cleaned_data.get('student_id')

        if student_id:
            try:
                Student.objects.get(sis_user_id__contains=str(student_id))
            except Student.DoesNotExist:
                raise forms.ValidationError("Student ID does not exist")
        return cleaned_data
    
class CourseForm(forms.Form):
    """
    This has a choice field containing all of the courses for the student.
    The student_id is in the url and should be used to get all the enrollment objects that belong to the student.
    Use a Choice Field to display the courses (not a ModelChoiceField).
    """

    def __init__(self, *args, **kwargs):
        student_id = kwargs.pop('student_id', None)
        super(CourseForm, self).__init__(*args, **kwargs)

        choices=[(enrollment.canvas_course_id, enrollment.course) for enrollment in Enrollment.objects.filter(sis_user_id__contains=student_id)]
        print("choices:", choices)
        self.fields['course'] = forms.ChoiceField(
            choices=choices
            )



class AssignmentForm(forms.Form):
    """
    Create a Model Form using the Extension model.

    This has a dropdown field containing all of the assignments for the course.
    The course_canvas_id is in the url and is used to get all the assignments that belong to the course.
    Only list assignments if they are active.
    Use a ChoiceField to display the assignments (not a ModelChoiceField).
    """

    
    def __init__(self, *args, **kwargs):
        print("kwargs:", kwargs)
        print("args:", args)
        
        course_canvas_id = kwargs.pop('course_canvas_id', None)
        student_id = kwargs.pop('student_id', None)
        root = kwargs.pop('root', None)
        self.root = root
        super(AssignmentForm, self).__init__(*args, **kwargs)

        assignments = [x.id for x in Assignment.objects.filter(course__course_id=course_canvas_id, active=True, quiz=False) if x.due_at]
        queryset = Assignment.objects.filter(pk__in=assignments)
        if root=='elp':
            choices=[(assignment.assignment_id, assignment.assignment_name) for assignment in queryset.filter(due_at__lte=datetime.datetime.now()) if datetime.datetime.now() < (assignment.due_at.replace(tzinfo=None) + datetime.timedelta(weeks=2))]

        if root=='extensions':
            choices=[(assignment.assignment_id, assignment.assignment_name) for assignment in queryset.filter(due_at__gte=datetime.datetime.now()) if datetime.datetime.now() > (assignment.due_at.replace(tzinfo=None) - datetime.timedelta(weeks=2))]

        self.fields['assignment'] = forms.ChoiceField(
            choices=choices
            )            
        self.fields['reason'] = forms.CharField(
            widget=forms.Textarea, 
            max_length=1000, 
            help_text= 'Max 1000 characters.'
            )
        
        if root == 'elp':
            self.fields['late_ignore'] = forms.BooleanField(
                required=False,
                label="Less than 5 minutes late?",
                help_text="Please indicate here if you submitted your assignment less than 5 minutes late. You are not required to provide evidence for such applications."
                )

            student = Student.objects.get(sis_user_id__contains=str(student_id))

            # get current datetime
            now = datetime.datetime.now()

            # get Date objects that are active and have a start date before now and a finish date after now
            date = Date.objects.get(start__lte=now, finish__gte=now)
            print("Dates:", date.start, date.finish, now)

            # get count of approved exemptions from late penalties for the student that are within the current date range and have no files attached
            count = Extension.objects.filter(student=student, extension_deadline__lte=date.finish, extension_deadline__gte=date.start, approved=True, files__exact="", extension_type__contains="ELP").exclude(late_ignore=True).count()

            print("count:", count, "hello")

            if count <2:
                file_required = False
                file_help_text = "If you choose not to upload evidence (e.g. medical note/certificate) then this application will be considered as one of two self-certified ELPs."
            else:
                file_required = True
                file_help_text = "You have already utilised two self-certified applications for the current period. You must upload evidence (e.g. a medical note/certificate) to support your application."


            self.fields['files'] = forms.FileField(
            label="Evidence upload",
            help_text=file_help_text,
            required=False
            )

            if count <2:
                self.fields['confirm_self_certified'] = forms.BooleanField(
                    required=True,
                    label= "Confirmation",
                    help_text="I understand that if I choose to submit this form without evidence my application will be considered as one of two self-certified ELPs available to me during this academic year."
                    )
                
    def clean(self):
            cleaned_data = super().clean()
            files = cleaned_data.get('files')
            checkbox = cleaned_data.get('late_ignore')
            confirmation = cleaned_data.get('confirm_self_certified')

            print(files, checkbox, confirmation)

            
            if self.root == 'elp':
                if not checkbox and not files and not confirmation:
                    raise forms.ValidationError("Please upload evidence.")

            return cleaned_data
        
        
  












    

 

