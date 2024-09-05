from django import forms
from .models import Assignment, Course

class CsvImportForm(forms.Form):
    csv_file = forms.FileField()

    # Add validation. Must be .csv file
    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']
        if not csv_file.name.endswith('.csv'):
            print("File is not a .csv file")
            raise forms.ValidationError('Please upload a .csv file')
        return csv_file


from django.forms.widgets import DateInput, TimeInput


class AssignmentDatesUpdateForm(forms.Form):
    unlock_date = forms.DateField(
        required=False,
        widget=DateInput(
            attrs={'type': 'date', 'class': 'form-control'}
        )
    )

    unlock_time = forms.DateField(
        required=False,
        widget=TimeInput(
            attrs={'type': 'time', 'class': 'form-control'}
        )
    )

    deadline_date = forms.DateField(
        required=False,
        widget=DateInput(
            attrs={'type': 'date', 'class': 'form-control'}
        )
    )

    deadline_time = forms.DateField(
        required=False,
        widget=TimeInput(
            attrs={'type': 'time', 'class': 'form-control'}
        )
    )

    lock_date = forms.DateField(
        required=False,
        widget=DateInput(
            attrs={'type': 'date', 'class': 'form-control'}
        )
    )

    lock_time = forms.DateField(
        required=False,
        widget=TimeInput(
            attrs={'type': 'time', 'class': 'form-control'}
        )
    )

    only_visible_to_overrides = forms.BooleanField(initial=False, required=False)



    




class AssignResitForm(forms.Form):
    """
    Create a form to select a course.
    Order the queryset by course_code, alphabetially.
    """

    resit_course = forms.ModelChoiceField(queryset=Course.objects.all().order_by('course_code'), empty_label=None)







