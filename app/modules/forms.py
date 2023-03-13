from django import forms
from django.contrib.admin.widgets import AdminDateWidget
from django.forms.widgets import DateInput, TimeInput

class ModulesSearchForm(forms.Form):
    search = forms.CharField()

class ModulesUpdateForm(forms.Form):
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
    force_publish = forms.BooleanField(required=False, 
                                       help_text="</br>If any of the selected modules are currently unpublished, you can publish them by checking this box."
                                       )
    
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