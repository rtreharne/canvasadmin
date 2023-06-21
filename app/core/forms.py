from django import forms
from .models import Assignment, Course

class CsvImportForm(forms.Form):
    csv_file = forms.FileField()


from django.forms.widgets import DateInput, TimeInput


class AssignmentDatesUpdateForm(forms.Form):
    unlock_date = forms.DateField(
        widget=DateInput(
            attrs={'type': 'date', 'class': 'form-control'}
        )
    )
    unlock_time = forms.DateField(
        widget=TimeInput(
            attrs={'type': 'time', 'class': 'form-control'}
        )
    )

class AssignResitForm(forms.Form):
    """
    Create a form to select a course.
    Order the queryset by course_code, alphabetially.
    """

    resit_course = forms.ModelChoiceField(queryset=Course.objects.all().order_by('course_code'), empty_label=None)







