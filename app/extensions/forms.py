from django import forms
from core.models import Student, Assignment
from enrollments.models import Enrollment
from extensions.models import Extension

class CsvImportForm(forms.Form):
    csv_file = forms.FileField()

class StudentIdForm(forms.Form):
    """
    This form should have a single field: student_id (int).
    It should be validated against the sis_user_id field in the Student model.
    The input integer should be 9 digits long and should be in the string of the sis_user_id field.
    """
    student_id = forms.IntegerField()

    def clean_student_id(self):
        student_id = self.cleaned_data['student_id']
        if len(str(student_id)) != 9:
            raise forms.ValidationError("Student ID must be 9 digits long")
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
    Use a ChoiceField to display the options (1 week, 2 weeks)
    """

    def __init__(self, *args, **kwargs):
        course_canvas_id = kwargs.pop('course_canvas_id', None)
        super(AssignmentForm, self).__init__(*args, **kwargs)
        choices=[(assignment.assignment_id, assignment.assignment_name) for assignment in Assignment.objects.filter(course__course_id=course_canvas_id, active=True)]
        self.fields['assignment'] = forms.ChoiceField(
            choices=choices
            )
        self.fields['extension_type'] = forms.ChoiceField(
            choices=[('EXTENSION', 'Extension'), ('ELP', 'Exemption from late penalty (ELP)')]
            )
        self.fields['extension'] = forms.ChoiceField(
            choices=[(1, '1 week'), (2, '2 weeks')]
            )
        self.fields['reason'] = forms.CharField(
            widget=forms.Textarea
            )
        self.fields['files'] = forms.FileField(
            required=False
            )
        













    

 

