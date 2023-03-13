from django import forms

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