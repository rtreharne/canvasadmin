from django.contrib import admin
from datetime import datetime, timedelta

def find_term_start_date(year):
    d = datetime(year, 1, 7)
    offset = -d.weekday() #weekday = 0 means monday
    start_year =  d + timedelta(offset)
    today = datetime.today()
    term_start = start_year + timedelta(days=38*7)
    if term_start > today:
        term_start = start_year - timedelta(days=(14*7))

    return term_start

class AssignmentDateFilter(admin.SimpleListFilter):
    title = 'Date Filter'
    parameter_name = 'due_at'

    def lookups(self, request, model_admin):
        return (
            ("s1_c1", "Semester 1, Cycle 1"),
            ('upcoming', 'Upcoming'),
            ('this_week', 'This week'),
            ('next_two_weeks', 'Next two weeks'),
            ('next_three_weeks', 'Next three weeks'),
            ('next_four_weeks', 'Next four weeks'),
            ('previous', 'Previous'),
            ('last_week', 'Last Week'),
            ('last_two_weeks', 'Last two week'),
            ('last_three_weeks', 'Last three weeks'),
            ('last_four_weeks', 'Last four weeks')
            
        )

    def queryset(self, request, queryset):
        today = datetime.today().date()
        last_monday = today - timedelta(days=today.weekday())
        

        value = self.value()
        term_start = find_term_start_date(today.year)
        if value == "s1_c1":
            pass
        if value == 'upcoming':
            return queryset.filter(due_at__gt=datetime.now())
        if value == 'this_week':
            return queryset.filter(due_at__gt=last_monday, due_at__lt=last_monday+timedelta(days=7))
        if value == 'next_two_weeks':
            return queryset.filter(due_at__gt=last_monday, due_at__lt=last_monday+timedelta(days=14))
        if value == 'next_three_weeks':
            return queryset.filter(due_at__gt=last_monday, due_at__lt=last_monday+timedelta(days=21))
        if value == 'next_four_weeks':
            return queryset.filter(due_at__gt=last_monday, due_at__lt=last_monday+timedelta(days=28))

        if value == 'previous':
            return queryset.filter(due_at__lt=datetime.now())
        if value == 'last_week':
            return queryset.filter(due_at__lt=last_monday, due_at__gt=last_monday-timedelta(days=7))
        if value == 'last_two_weeks':
            return queryset.filter(due_at__lt=datetime.now(), due_at__gt=last_monday-timedelta(days=14))
        if value == 'last_three_weeks':
            return queryset.filter(due_at__lt=datetime.now(), due_at__gt=last_monday-timedelta(days=21))
        if value == 'next_four_weeks':
            return queryset.filter(due_at__lt=datetime.now(), due_at__gt=last_monday-timedelta(days=28))




